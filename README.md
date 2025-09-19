# LawMan

LawMan is an end-to-end workflow for turning long-form legal documents into queryable knowledge. It ingests contracts, extracts clause-level structure, enriches the text with lightweight information extraction, indexes the results in hybrid search backends, exposes them through a FastAPI service, and surfaces the experience in a Next.js dashboard. Optional tooling can also project the same enriched data into a Neo4j knowledge graph.

## Table of Contents
- [System Overview](#system-overview)
- [Component Breakdown](#component-breakdown)
- [End-to-End Data Flow](#end-to-end-data-flow)
- [Local Development Setup](#local-development-setup)
- [Running the Ingestion Pipeline](#running-the-ingestion-pipeline)
- [API Reference](#api-reference)
- [Frontend Application](#frontend-application)
- [Knowledge Graph Export (Optional)](#knowledge-graph-export-optional)
- [Troubleshooting](#troubleshooting)

## System Overview
LawMan is organised as a collection of Python services and a React/Next.js frontend. At a high level the project delivers:

```
PDF contract → Docling parsing → Clause JSON → Lightweight IE enrichment →
OpenSearch (BM25) + Qdrant (dense) indexing → FastAPI (ingest + ask) → Next.js UI /
Postman collection → Optional Neo4j knowledge graph
```

- **Backend (`backend/app`)** provides REST endpoints for ingesting pre-parsed clause JSON and for running hybrid (BM25 + semantic) clause search with optional cross-encoder reranking.
- **Services (`backend/app/services`)** hold the offline jobs: PDF parsing, clause enrichment, hybrid retrieval, reranker, ingestion into OpenSearch/Qdrant, and KG export tooling.
- **Frontend (`frontend`)** is a Next.js 14 application that offers a document dashboard with upload affordances, clause viewer, summaries, and an AI assistance surface.
- **Infrastructure** is provisioned locally via `docker-compose.yml` which spins up OpenSearch (two-node cluster + Dashboards UI) and Qdrant. Neo4j can be run externally if you need graph visualisation.

## Component Breakdown

### Document Parsing & Enrichment
- **`services/parsing.py`** orchestrates Docling PDF parsing, clause segmentation, and page/line anchoring.
- **`services/ie.py`** applies regex heuristics to annotate each clause with parties, monetary amounts, dates, references, obligations, and a coarse topic label.
- Outputs live beside the scripts (`contract_parsed.json`, `contract_ie.json`) for convenience.

### Storage & Retrieval
- **OpenSearch (`services/retrieval.py`)** stores the clause documents for lexical/BM25 search, with helpers for index creation and highlighting.
- **Qdrant (`services/vector_search.py`)** stores dense embeddings created with `BAAI/bge-m3`, enabling multilingual semantic search.
- **Hybrid search (`services/hybrid_search.py`)** combines BM25 and dense scores (weight controlled by `alpha`) and returns the fused list.
- **Reranking (`services/reranker.py`)** optionally re-sorts the top clauses using the `BAAI/bge-reranker-base` cross-encoder.

### API Layer
- **FastAPI app (`backend/app/main.py`)** wires the routes, provides `/healthz`, and configures permissive CORS for local tooling.
- **Routers (`backend/app/routers/ingest.py`, `backend/app/routers/ask.py`)** expose `/ingest` for bulk indexing and `/ask` for querying.
- **Schemas (`backend/app/schemas.py`)** define request/response contracts that the frontend and Postman share.

### Frontend
- **Next.js dashboard (`frontend/src/app/dashboard/page.tsx`)** hosts the core UX with panels for document viewing, summary, and AI chat.
- **Landing page (`frontend/src/app/page.tsx`)** markets the assistant.
- UI components live in `frontend/src/components`, and styling is handled via Tailwind.

### Knowledge Graph
- **`services/kg.py`** converts the IE-enriched clauses into node/edge JSON suitable for Neo4j ingestion.
- **`services/kg_neo4j_loader.py`** loads the generated graph into Neo4j using the official Python driver, creating basic constraints.

## End-to-End Data Flow
1. **Parse contract**: `parsing.py` converts a PDF (default `contract.pdf`) into structured clause records with page and line anchors.
2. **Enrich clauses**: `ie.py` augments each clause with heuristic IE metadata.
3. **Index data**: `ingestion.py` (via `/ingest` or CLI) pushes clause JSON into both OpenSearch and Qdrant.
4. **Query**: `/ask` performs hybrid search across the indexed stores and can rerank results with a cross-encoder.
5. **Present**: The frontend consumes the API for interactive querying, and Postman collections can be used for manual regression/testing.
6. *(Optional)* **Graph export**: `kg.py` and `kg_neo4j_loader.py` project the enriched clauses into a Neo4j graph for downstream analytics.

## Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and `pnpm`
- Docker Desktop or compatible engine (for OpenSearch and Qdrant)
- `pip`, `uvicorn`, and `pnpm` binaries on your PATH

### Backend Environment
1. **Clone and create a virtual environment**
   ```bash
   git clone <repo-url>
   cd law-man
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Configure environment variables**
   - Copy `.env.example` if present, or create `.env` with at least:
     ```dotenv
     OPENSEARCH_INITIAL_ADMIN_PASSWORD=<admin-password>
     QDRANT_HOST=localhost
     QDRANT_PORT=6333
     NEO4J_URI=bolt://localhost:7687      # optional
     NEO4J_USER=neo4j                     # optional
     NEO4J_PASSWORD=<neo4j-password>      # optional
     ```
3. **Start dependencies**
   ```bash
   docker compose up -d opensearch-node1 opensearch-node2 opensearch-dashboards qdrant
   ```
   - OpenSearch will expose HTTPS on `https://localhost:9200` (basic auth `admin/<password>`).
   - Qdrant listens on `http://localhost:6333`.
4. **Run the API**
   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   The interactive docs will be at `http://localhost:8000/docs`.

### Frontend Environment
1. ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```
2. Visit `http://localhost:3000` to explore the dashboard.
3. To point the UI at the backend, configure a `.env.local` with e.g. `NEXT_PUBLIC_API_URL=http://localhost:8000` (if you add fetch calls).

## Running the Ingestion Pipeline
You can exercise the pipeline entirely from the command line.

1. **Parse a PDF into clauses**
   ```bash
   python backend/app/services/parsing.py --pdf contract.pdf --out backend/app/services/contract_parsed.json
   ```
2. **Enrich with IE metadata**
   ```bash
   python backend/app/services/ie.py --input backend/app/services/contract_parsed.json --output backend/app/services/contract_ie.json
   ```
3. **Ingest into OpenSearch + Qdrant**
   ```bash
   python backend/app/services/ingest_ie.py --json backend/app/services/contract_ie.json --index contracts
   ```
   - The same ingestion logic is used by the `/ingest` API route.

## API Reference

### `GET /healthz`
- Health probe used by orchestration and smoke tests.
- Response: `{ "status": "ok" }`

### `POST /ingest`
- Body (`application/json`):
  ```json
  {
    "json_path": "backend/app/services/contract_ie.json",
    "index_name": "contracts",
    "reset": true
  }
  ```
- Behaviour: reads the clause JSON, indexes into OpenSearch and Qdrant. `reset=true` recreates both stores.
- Response:
  ```json
  {
    "indexed": 123,
    "index_name": "contracts",
    "qdrant_collection": "contracts",
    "reset": true,
    "message": "Indexed 123 clauses from contract_ie.json"
  }
  ```

### `POST /ask`
- Body:
  ```json
  {
    "query": "termination for convenience",
    "top_k": 10,
    "alpha": 0.6,
    "rerank": true
  }
  ```
- Behaviour: runs BM25 + vector hybrid search, fuses scores (`alpha` controls lexical weight), and optionally reranks via cross-encoder.
- Response (simplified):
  ```json
  {
    "query": "termination for convenience",
    "top_k": 10,
    "alpha": 0.6,
    "reranked": true,
    "results": [
      {
        "contract_id": "contract.pdf",
        "clause_id": "c12",
        "heading": "TERMINATION",
        "text_snippet": "Either party may terminate...",
        "page": 5,
        "line_range": [40, 58],
        "bm25_score": 0.78,
        "vec_score": 0.66,
        "hybrid_score": 0.72,
        "reranker_score": 14.2,
        "highlight": ["Either party may terminate..."]
      }
    ]
  }
  ```
- Usage: ideal for Postman collections or frontend fetches.

## Frontend Application
- Located in `frontend/` with a conventional Next.js 14 app router structure.
- `src/app/dashboard/page.tsx` controls the main logged-in experience, currently wired with mocked state and sample assets. Hook it up to the API by adding fetch hooks to `/ask` and `/ingest`.
- Components in `src/components/Dashboard` cover upload, document viewing, AI chat, and summaries. Tailwind utilities live in `src/app/globals.css`.

## Knowledge Graph Export (Optional)
1. Generate IE-enriched clauses (as above).
2. Build node/edge JSON:
   ```bash
   python backend/app/services/kg.py --input backend/app/services/contract_ie.json --out-nodes backend/app/services/kg_nodes.json --out-edges backend/app/services/kg_edges.json
   ```
3. Load into Neo4j (ensure a Neo4j instance is running):
   ```bash
   python backend/app/services/kg_neo4j_loader.py --nodes backend/app/services/kg_nodes.json --edges backend/app/services/kg_edges.json --uri bolt://localhost:7687 --user neo4j --password <password>
   ```
4. Explore relationships in Neo4j Browser or Bloom.

## Troubleshooting
- **OpenSearch refuses connection**: confirm the containers are healthy (`docker compose ps`) and that `OPENSEARCH_INITIAL_ADMIN_PASSWORD` in your `.env` matches the compose file.
- **Vector ingestion fails**: ensure Qdrant is running and the SentenceTransformer model can be downloaded (requires network access on first run).
- **Slow ingestion with reranker**: the cross-encoder runs on CPU by default; consider batching queries or provisioning a GPU-enabled environment.
- **Docling OCR errors**: install Tesseract CLI (`sudo apt install tesseract-ocr`) and ensure it is discoverable in `PATH`.
- **Neo4j load issues**: verify Bolt URI and credentials; constraints will be created automatically on first load.

---
If you need additional guidance (Postman collections, deployment scripts, etc.), open an issue or reach out to the contributors listed in the workspace.
