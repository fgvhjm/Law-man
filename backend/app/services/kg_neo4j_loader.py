#!/usr/bin/env python3
"""
Load KG JSON (kg_nodes.json, kg_edges.json) into Neo4j.

Requires the Python driver:
  pip install neo4j

Env vars (or CLI flags):
  NEO4J_URI       (default: bolt://localhost:7687)
  NEO4J_USER      (default: neo4j)
  NEO4J_PASSWORD  (required if auth enabled)

Example:
  export NEO4J_PASSWORD='Neo4j_Pass123!'
  python3 kg_neo4j_loader.py \
    --nodes kg_nodes.json --edges kg_edges.json \
    --uri bolt://localhost:7687 --user neo4j --password "$NEO4J_PASSWORD"
"""

from __future__ import annotations

import os
import json
import argparse
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

try:
    from neo4j import GraphDatabase
except Exception as e:  # pragma: no cover
    raise SystemExit("Please install the neo4j driver: pip install neo4j") from e


def _constraints(session):
    # Create uniqueness constraints for important labels
    session.run("CREATE CONSTRAINT contract_id IF NOT EXISTS FOR (n:Contract) REQUIRE n.contract_id IS UNIQUE")
    session.run("CREATE CONSTRAINT clause_key IF NOT EXISTS FOR (n:Clause) REQUIRE (n.contract_id, n.clause_id) IS UNIQUE")
    session.run("CREATE CONSTRAINT party_name IF NOT EXISTS FOR (n:Party) REQUIRE n.name IS UNIQUE")
    # Not strictly unique, but helps performance if present
    # session.run("CREATE INDEX obligation_text IF NOT EXISTS FOR (n:Obligation) ON (n.text)")


def load_nodes(tx, nodes: list[Dict[str, Any]]):
    for n in nodes:
        typ = n.get("type")
        props = {k: v for k, v in n.items() if k not in {"id", "type"}}
        if typ == "Contract":
            tx.run("MERGE (c:Contract {contract_id: $contract_id})", **props)
        elif typ == "Clause":
            tx.run(
                "MERGE (c:Clause {contract_id: $contract_id, clause_id: $clause_id}) "
                "SET c += $props",
                contract_id=props.get("contract_id"),
                clause_id=props.get("clause_id"),
                props=props,
            )
        elif typ == "Party":
            tx.run("MERGE (p:Party {name: $name})", **props)
        elif typ == "Obligation":
            tx.run("MERGE (o:Obligation {text: $text})", **props)
        elif typ == "Amount":
            tx.run("MERGE (a:Amount {raw: $raw}) SET a += $props", props=props, raw=props.get("raw"))
        elif typ == "Date":
            tx.run("MERGE (d:Date {text: $text})", **props)
        elif typ == "Reference":
            tx.run("MERGE (r:Reference {text: $text})", **props)


def load_edges(tx, edges: list[Dict[str, Any]]):
    for e in edges:
        et = e.get("type")
        src = e.get("src")
        dst = e.get("dst")
        # We need the identifying props for endpoints; include them on nodes in JSON
        # To avoid round-trips, match by known keys per type
        # For simplicity, we re-materialize endpoints from their properties present in nodes already loaded.
        # Edges are created by looking up any node by id in an auxiliary label :_Temp with property id.
        # Simpler approach: pass through ids using an in-memory map is not available here.
        # Instead, we create an ID index during load by setting :_Temp{id:<id>} on each node.
        # That index is created in load_nodes phase below.
        pass  # Placeholder; actual edge creation is done in a consolidated step after stamping ids.


STAMP_IDS_QUERY = """
CALL {
  WITH $nodes AS nodes
  UNWIND nodes AS n
  WITH n
  CALL {
    WITH n
    WITH n WHERE n.type = 'Contract'
    MERGE (x:Contract {contract_id: n.contract_id})
    SET x._kid = n.id
    RETURN 1 AS contract_result
  }
  CALL {
    WITH n
    WITH n WHERE n.type = 'Clause'
    MERGE (x:Clause {contract_id: n.contract_id, clause_id: n.clause_id})
    SET x._kid = n.id
    RETURN 1 AS clause_result
  }
  CALL {
    WITH n
    WITH n WHERE n.type = 'Party'
    MERGE (x:Party {name: n.name})
    SET x._kid = n.id
    RETURN 1 AS party_result
  }
  CALL {
    WITH n
    WITH n WHERE n.type = 'Obligation'
    MERGE (x:Obligation {text: n.text})
    SET x._kid = n.id
    RETURN 1 AS obligation_result
  }
  CALL {
    WITH n
    WITH n WHERE n.type = 'Amount'
    MERGE (x:Amount {raw: n.raw})
    SET x._kid = n.id
    RETURN 1 AS amount_result
  }
  CALL {
    WITH n
    WITH n WHERE n.type = 'Date'
    MERGE (x:Date {text: n.text})
    SET x._kid = n.id
    RETURN 1 AS date_result
  }
  CALL {
    WITH n
    WITH n WHERE n.type = 'Reference'
    MERGE (x:Reference {text: n.text})
    SET x._kid = n.id
    RETURN 1 AS reference_result
  }
  RETURN 1 AS node_result
}
RETURN 1 AS overall_result
"""


CREATE_EDGES_QUERY = """
WITH $edges AS edges
UNWIND edges AS e
MATCH (s {_kid: e.src}), (t {_kid: e.dst})
CALL {
  WITH e, s, t
  WITH e, s, t WHERE e.type = 'CONTAINS'
  MERGE (s)-[:CONTAINS]->(t)
}
CALL {
  WITH e, s, t
  WITH e, s, t WHERE e.type = 'MENTIONS_PARTY'
  MERGE (s)-[:MENTIONS_PARTY]->(t)
}
CALL {
  WITH e, s, t
  WITH e, s, t WHERE e.type = 'OBLIGATES'
  MERGE (s)-[:OBLIGATES]->(t)
}
CALL {
  WITH e, s, t
  WITH e, s, t WHERE e.type = 'DEFINED_IN'
  MERGE (s)-[:DEFINED_IN]->(t)
}
CALL {
  WITH e, s, t
  WITH e, s, t WHERE e.type = 'HAS_AMOUNT'
  MERGE (s)-[:HAS_AMOUNT]->(t)
}
CALL {
  WITH e, s, t
  WITH e, s, t WHERE e.type = 'HAS_DATE'
  MERGE (s)-[:HAS_DATE]->(t)
}
CALL {
  WITH e, s, t
  WITH e, s, t WHERE e.type = 'REFERENCES'
  MERGE (s)-[:REFERENCES]->(t)
}
RETURN count(*) AS relationships_created
"""


def main():
    load_dotenv()  # pull in Neo4j connection settings from a local .env if present
    here = Path(__file__).resolve().parent
    default_nodes = here / "kg_nodes.json"
    default_edges = here / "kg_edges.json"

    ap = argparse.ArgumentParser(description="Load KG JSON into Neo4j")
    ap.add_argument("--nodes", default=str(default_nodes), help="Path to kg_nodes.json")
    ap.add_argument("--edges", default=str(default_edges), help="Path to kg_edges.json")
    ap.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    ap.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    ap.add_argument("--password", default=os.getenv("NEO4J_PASSWORD"))
    args = ap.parse_args()

    nodes = json.loads(Path(args.nodes).read_text(encoding="utf-8"))
    edges = json.loads(Path(args.edges).read_text(encoding="utf-8"))

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    with driver.session() as session:
        _constraints(session)
        # Stamp IDs on nodes so we can match edges by src/dst id
        session.run(STAMP_IDS_QUERY, nodes=nodes)
        # Create relationships
        res = session.run(CREATE_EDGES_QUERY, edges=edges)
        try:
            print(res.single())
        except Exception:
            pass
    driver.close()
    print("✅ Loaded KG into Neo4j")


if __name__ == "__main__":
    main()
