#!/usr/bin/env python3
"""
Ingest IE-enriched clauses into OpenSearch and Qdrant.

Defaults to contract_ie.json next to this script.
Usage:
  python3 ingest_ie.py
  python3 ingest_ie.py --json /path/to/contract_ie.json --index contracts --no-reset
"""

from pathlib import Path
import argparse

try:
    from .ingestion import ingest
except ImportError:
    from ingestion import ingest


def main():
    here = Path(__file__).resolve().parent
    default_json = here / "contract_ie.json"

    parser = argparse.ArgumentParser(description="Ingest IE-enriched clauses into OpenSearch and Qdrant")
    parser.add_argument(
        "--json",
        dest="json_file",
        type=str,
        default=str(default_json),
        help=f"Path to IE-enriched JSON (default: {default_json})",
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
        help="Do not recreate the index/collection before ingesting",
    )

    args = parser.parse_args()
    ingest(args.json_file, reset=args.reset, index_name=args.index_name)


if __name__ == "__main__":
    main()

