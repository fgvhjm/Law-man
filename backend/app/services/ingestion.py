import json
from retrieval import init_client, create_index, bulk_index
from vector_search import VectorStore


def ingest(json_file, reset=True):
    # Load JSON (Docling output)
    with open(json_file, "r", encoding="utf-8") as f:
        clauses = json.load(f)

    # --- OpenSearch Ingestion ---
    client = init_client()
    create_index(client, "contracts")
    bulk_index(client, clauses, "contracts", reset=reset)

    # --- Qdrant Ingestion ---
    vs = VectorStore(reset=reset)
    vs.index_clauses(clauses)

    print(f"Indexed {len(clauses)} clauses into both OpenSearch and Qdrant")


if __name__ == "__main__":
    #Path to your Docling JSON
    json_file = "/Users/amitprasadsingh/Desktop/opensearch/contract_parsed.json"
    ingest(json_file, reset=True)
