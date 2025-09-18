import os
import uuid
import json
from typing import List, Dict

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import OptimizersConfigDiff

load_dotenv()


class VectorStore:
    def __init__(
        self,
        qdrant_host: str = os.getenv("QDRANT_HOST", "localhost"),
        qdrant_port: int = int(os.getenv("QDRANT_PORT", 6333)),
        collection_name: str = "contracts",
        embedder_model: str = "BAAI/bge-m3",  # ✅ multilingual model
        batch_size: int = 256,
        reset: bool = False,
    ):
        self.collection = collection_name
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)

        # load multilingual model
        self.embedder = SentenceTransformer(embedder_model, device="cpu", trust_remote_code=True)

        # model vector dimension
        self.vector_size = self.embedder.get_sentence_embedding_dimension()
        self.batch_size = batch_size

        # check or create collection
        existing = [c.name for c in self.client.get_collections().collections]

        if reset or not self.client.collection_exists(self.collection):
            if self.client.collection_exists(self.collection):
                self.client.delete_collection(self.collection)

            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                optimizers_config=OptimizersConfigDiff(memmap_threshold=20000),  # optional tuning
            )
            print(f"🔄 Created Qdrant collection: {self.collection} (dim={self.vector_size})")

    def _embed(self, texts: List[str], batch_size: int = 4) -> List[List[float]]:
        vectors = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            emb = self.embedder.encode(
                chunk,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=batch_size,
            )
            vectors.extend(emb.tolist())
        return vectors

    def index_clauses(self, clauses: List[Dict]):
        texts = [c.get("text", "") for c in clauses]
        vectors = self._embed(texts)

        points = []
        for c, vec in zip(clauses, vectors):
            cid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{c['contract_id']}#{c['clause_id']}"))
            points.append(PointStruct(id=cid, vector=vec, payload=c))

        for i in range(0, len(points), self.batch_size):
            batch = points[i : i + self.batch_size]
            self.client.upsert(collection_name=self.collection, points=batch)

        print(f"📄 Indexed {len(clauses)} clauses into Qdrant collection '{self.collection}'")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        vec = self._embed([query])[0]
        res = self.client.query_points(
            collection_name=self.collection,
            query=vec,
            limit=top_k,
            with_vectors=False  # optional, saves bandwidth
        )
        return [
            {"score": p.score, "payload": p.payload}
            for p in res.points
        ]

    def format_qdrant_results(self, results):
        formatted = []
        for r in results:
            p = r["payload"]
            formatted.append({
                "contract_id": p.get("contract_id"),
                "clause_id": p.get("clause_id"),
                "heading": p.get("heading"),
                "text_snippet": p.get("text", "")[:400],
                "page": p.get("page"),
                "line_range": [p.get("line_start"), p.get("line_end")],
                "lang": p.get("lang", "en"),
                "score": r["score"],
                "highlight": []  # vector search doesn’t give highlights
            })
        return formatted



if __name__ == "__main__":
    json_file = "/Users/amitprasadsingh/Desktop/opensearch/contract_parsed.json"
    with open(json_file, "r", encoding="utf-8") as f:
        clauses = json.load(f)

    vs = VectorStore(reset=True)
    vs.index_clauses(clauses)

    raw_hits = vs.search("बीमा सुरक्षा", top_k=10)
    formatted_hits = vs.format_qdrant_results(raw_hits)
    print(type(formatted_hits))

    output_file = "qdrant_search_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(formatted_hits, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(formatted_hits)} results to {output_file}")
