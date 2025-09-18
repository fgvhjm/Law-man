import json
from pathlib import Path
import argparse
from retrieval import init_client, create_index, bulk_index
from vector_search import VectorStore


def ingest(json_file, reset=True, index_name: str = "contracts"):
    # Load JSON (Docling output)
    with open(json_file, "r", encoding="utf-8") as f:
        clauses = json.load(f)

    # --- OpenSearch Ingestion ---
    client = init_client()
    create_index(client, index_name)
    bulk_index(client, clauses, index_name, reset=reset)

    # --- Qdrant Ingestion ---
    vs = VectorStore(reset=reset, collection_name=index_name)
    vs.index_clauses(clauses)

    print(f"Indexed {len(clauses)} clauses into OpenSearch and Qdrant collection '{index_name}'")


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    default_json = here / "contract_parsed.json"

    parser = argparse.ArgumentParser(description="Ingest parsed clauses into OpenSearch and Qdrant")
    parser.add_argument(
        "--json",
        dest="json_file",
        type=str,
        default=str(default_json),
        help=f"Path to clauses JSON (default: {default_json})",
    )
    parser.add_argument(
        "--index",
        dest="index_name",
        type=str,
        default="contracts",
        help="Index/collection name (default: contracts)",
    )
    parser.add_argument(
        "--no-reset",
        dest="reset",
        action="store_false",
        help="Do not recreate index/collection before ingesting",
    )
    args = parser.parse_args()

    ingest(args.json_file, reset=args.reset, index_name=args.index_name)
