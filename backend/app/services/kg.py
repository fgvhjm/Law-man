#!/usr/bin/env python3
"""
Knowledge Graph builder for IE‑enriched clauses.

Input:  IE JSON from ie.py (default: contract_ie.json)
Output: Two JSON files with deduplicated nodes and edges:
  - kg_nodes.json
  - kg_edges.json

Node types:
  - Contract(id)
  - Clause(id, contract_id, clause_id, heading, page, line_start, line_end)
  - Party(name)
  - Obligation(text)
  - Amount(value, currency, unit, raw)
  - Date(text)
  - Reference(text)

Edge types:
  - CONTAINS       Contract -> Clause
  - MENTIONS_PARTY Clause   -> Party
  - OBLIGATES      Party    -> Obligation
  - DEFINED_IN     Obligation -> Clause
  - HAS_AMOUNT     Clause   -> Amount
  - HAS_DATE       Clause   -> Date
  - REFERENCES     Clause   -> Reference

Deterministic IDs are generated so repeated runs are stable.
No external dependencies.
"""

from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple


# ---------- ID helpers ----------

def _sid(kind: str, value: str) -> str:
    """Stable ID from kind + value using SHA1 prefix (12 chars)."""
    h = hashlib.sha1(f"{kind}|{value}".encode("utf-8")).hexdigest()[:12]
    return f"{kind}:{h}"


def node_key(kind: str, props: Dict[str, Any]) -> Tuple[str, str]:
    """Return (id, unique_key_text) for dedupe based on essential props per kind."""
    if kind == "Contract":
        u = str(props.get("contract_id") or props.get("id") or "")
    elif kind == "Clause":
        u = f"{props.get('contract_id')}#{props.get('clause_id')}"
    elif kind == "Party":
        u = (props.get("name") or "").strip()
    elif kind == "Obligation":
        u = (props.get("text") or "").strip()
    elif kind == "Amount":
        u = f"{props.get('value')}|{props.get('currency')}|{props.get('unit')}|{props.get('raw')}"
    elif kind == "Date":
        u = (props.get("text") or "").strip()
    elif kind == "Reference":
        u = (props.get("text") or "").strip()
    else:
        u = json.dumps(props, sort_keys=True)
    return _sid(kind, u), u


def add_node(nodes: Dict[str, Dict[str, Any]], kind: str, **props) -> str:
    nid, _ = node_key(kind, props)
    if nid not in nodes:
        nodes[nid] = {"id": nid, "type": kind, **props}
    return nid


def add_edge(edges: Dict[str, Dict[str, Any]], etype: str, src: str, dst: str, **props) -> str:
    eid = _sid(etype, f"{src}->{dst}|{json.dumps(props, sort_keys=True)}")
    if eid not in edges:
        edges[eid] = {"id": eid, "type": etype, "src": src, "dst": dst, **props}
    return eid


# ---------- Builder ----------

def build_kg(clauses: list[dict[str, Any]]) -> tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: Dict[str, Dict[str, Any]] = {}

    # Track created contract nodes to avoid duplicates
    for c in clauses:
        contract_id = c.get("contract_id") or "contract"
        clause_id = c.get("clause_id")
        heading = c.get("heading")
        page = c.get("page")
        line_start = c.get("line_start")
        line_end = c.get("line_end")

        # Contract
        n_contract = add_node(nodes, "Contract", contract_id=contract_id)

        # Clause
        n_clause = add_node(
            nodes,
            "Clause",
            contract_id=contract_id,
            clause_id=clause_id,
            heading=heading,
            page=page,
            line_start=line_start,
            line_end=line_end,
        )

        # Contract contains Clause
        add_edge(edges, "CONTAINS", n_contract, n_clause)

        # IE fields (may be missing)
        ie = c.get("ie") or {}

        # Parties
        for p in (ie.get("parties") or []):
            if not p:
                continue
            n_party = add_node(nodes, "Party", name=str(p))
            add_edge(edges, "MENTIONS_PARTY", n_clause, n_party)

        # Obligations
        obligations = ie.get("obligations") or []
        for ob_text in obligations:
            if not ob_text or len(ob_text) < 5:
                continue
            n_ob = add_node(nodes, "Obligation", text=ob_text)
            # If we saw parties, connect them to the obligation; otherwise just anchor to the clause
            party_ids = [node_id for node_id, data in nodes.items() if data["type"] == "Party"]
            if party_ids:
                for pid in party_ids:
                    add_edge(edges, "OBLIGATES", pid, n_ob)
            add_edge(edges, "DEFINED_IN", n_ob, n_clause)

        # Amounts
        for amt in (ie.get("amounts") or []):
            n_amt = add_node(
                nodes,
                "Amount",
                value=amt.get("value"),
                currency=amt.get("currency"),
                unit=amt.get("unit"),
                raw=amt.get("raw"),
            )
            add_edge(edges, "HAS_AMOUNT", n_clause, n_amt)

        # Dates
        for dtxt in (ie.get("dates") or []):
            n_date = add_node(nodes, "Date", text=dtxt)
            add_edge(edges, "HAS_DATE", n_clause, n_date)

        # References
        for rtxt in (ie.get("references") or []):
            n_ref = add_node(nodes, "Reference", text=rtxt)
            add_edge(edges, "REFERENCES", n_clause, n_ref)

    return nodes, edges


# ---------- IO ----------

def run(input_json: Path, out_nodes: Path, out_edges: Path) -> None:
    with input_json.open("r", encoding="utf-8") as f:
        clauses = json.load(f)
    nodes, edges = build_kg(clauses)

    with out_nodes.open("w", encoding="utf-8") as f:
        json.dump(list(nodes.values()), f, indent=2, ensure_ascii=False)
    with out_edges.open("w", encoding="utf-8") as f:
        json.dump(list(edges.values()), f, indent=2, ensure_ascii=False)

    # Print a small summary
    counts: Dict[str, int] = {}
    for n in nodes.values():
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    print(f"✅ Wrote {len(nodes)} nodes and {len(edges)} edges")
    print("Nodes by type:")
    for k in sorted(counts):
        print(f"  - {k}: {counts[k]}")


def main():
    here = Path(__file__).resolve().parent
    default_in = here / "contract_ie.json"
    default_nodes = here / "kg_nodes.json"
    default_edges = here / "kg_edges.json"

    p = argparse.ArgumentParser(description="Build a lightweight KG from IE‑enriched clauses")
    p.add_argument("--input", "--in", dest="input", default=str(default_in), help=f"Input IE JSON (default: {default_in})")
    p.add_argument("--out-nodes", dest="out_nodes", default=str(default_nodes), help=f"Output nodes JSON (default: {default_nodes})")
    p.add_argument("--out-edges", dest="out_edges", default=str(default_edges), help=f"Output edges JSON (default: {default_edges})")
    args = p.parse_args()

    run(Path(args.input), Path(args.out_nodes), Path(args.out_edges))


if __name__ == "__main__":
    main()

