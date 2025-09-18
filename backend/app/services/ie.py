#!/usr/bin/env python3
"""
Lightweight Information Extraction (IE) for contract clauses.

Reads clause records (from parsing.py) and enriches them with:
- parties (uppercase role-like tokens, common legal party names)
- amounts (currency amounts)
- durations (e.g., "30 days")
- dates (simple patterns like "Jan 1, 2025" or 2025-01-01)
- references (Section 1.2, Exhibit A, etc.)
- obligations (sentences containing shall/must/will)
- topic (coarse label by keywords: Insurance, Indemnification, Termination, Confidentiality, Payment, Scope)

Outputs an enriched JSON array alongside the input file by default.
No external dependencies; heuristic regex-only, fast and portable.
"""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse


# ---------- Helpers ----------

UPPER_PARTY_HINTS = {
    "CONSULTANT",
    "COMMISSION",
    "CLIENT",
    "COMPANY",
    "VENDOR",
    "SUPPLIER",
    "CUSTOMER",
    "LICENSOR",
    "LICENSEE",
    "LESSOR",
    "LESSEE",
    "PARTY",
    "PARTIES",
}

CAP_PARTY_HINTS = {
    "Consultant",
    "Commission",
    "Client",
    "Company",
    "Vendor",
    "Supplier",
    "Customer",
    "Licensor",
    "Licensee",
    "Lessor",
    "Lessee",
}

AMOUNT_RE = re.compile(
    r"(?:(?P<currency>USD|INR|EUR|GBP|AUD|CAD|Rs\.?|US\$|\$|£|€)\s*)?\b(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\b(?:\s*(?P<unit>million|billion|thousand|lakhs?|crores?))?",
    re.IGNORECASE,
)

DURATION_RE = re.compile(r"\b(?P<num>\d{1,3})\s*(?P<unit>day|days|month|months|year|years)\b", re.IGNORECASE)

# Dates: Month dd, yyyy | dd/mm/yyyy | yyyy-mm-dd (very naive)
DATE_RE = re.compile(
    r"\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
    re.IGNORECASE,
)

SECTION_RE = re.compile(r"\bSection\s+\d+(?:\.\d+)*\b", re.IGNORECASE)
EXHIBIT_RE = re.compile(r"\bExhibit\s+[A-Z]\b")

OBLIG_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
OBLIG_HINT = re.compile(r"\b(shall|must|will|is required to|agrees to|undertakes to)\b", re.IGNORECASE)


TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "Insurance": ["insurance", "coverage", "liability", "workers' compensation", "general liability"],
    "Indemnification": ["indemnify", "hold harmless", "defend"],
    "Termination": ["terminate", "termination", "notice", "breach"],
    "Confidentiality": ["confidential", "non-disclosure", "nda", "proprietary"],
    "Payment": ["fee", "payment", "invoice", "compensation", "price"],
    "Scope": ["scope of services", "duties", "responsibilities", "deliverables"],
}


def extract_parties(text: str, heading: str | None) -> List[str]:
    candidates = set()
    blob = (heading or "") + "\n" + (text or "")
    # Uppercase tokens heuristic
    for token in re.findall(r"[A-Z][A-Z\-]{3,}", blob):
        if token in UPPER_PARTY_HINTS or token.isupper():
            # keep some noisy upper tokens short
            if len(token) > 3:
                candidates.add(token)
    # Capitalized known roles
    for cap in CAP_PARTY_HINTS:
        if re.search(rf"\b{re.escape(cap)}\b", blob):
            candidates.add(cap)
    # Normalize to sorted list
    out = sorted(candidates)
    # Keep it short
    return out[:12]


def normalize_amount(amount: str, unit: str | None) -> float | None:
    try:
        amt = float(amount.replace(",", ""))
    except ValueError:
        return None
    if not unit:
        return amt
    u = unit.lower()
    if u.startswith("million"):
        return amt * 1_000_000
    if u.startswith("billion"):
        return amt * 1_000_000_000
    if u.startswith("thousand"):
        return amt * 1_000
    if u.startswith("lakh"):
        return amt * 100_000
    if u.startswith("crore"):
        return amt * 10_000_000
    return amt


def extract_amounts(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in AMOUNT_RE.finditer(text or ""):
        currency = m.group("currency")
        amount = m.group("amount")
        unit = m.group("unit")
        norm = normalize_amount(amount, unit)
        if amount is None:
            continue
        out.append(
            {
                "raw": m.group(0),
                "value": norm if norm is not None else amount,
                "currency": currency if currency else None,
                "unit": unit if unit else None,
            }
        )
    # dedupe by raw
    seen = set()
    deduped = []
    for a in out:
        if a["raw"] in seen:
            continue
        seen.add(a["raw"])
        deduped.append(a)
    return deduped[:20]


def extract_durations(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in DURATION_RE.finditer(text or ""):
        out.append({"num": int(m.group("num")), "unit": m.group("unit").lower(), "raw": m.group(0)})
    return out[:20]


def extract_dates(text: str) -> List[str]:
    dates = DATE_RE.findall(text or "")
    # Normalize whitespace
    return [d.strip() for d in dates][:20]


def extract_references(text: str) -> List[str]:
    refs = []
    refs += SECTION_RE.findall(text or "")
    refs += EXHIBIT_RE.findall(text or "")
    # dedupe
    seen = set()
    out = []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out[:20]


def extract_obligations(text: str) -> List[str]:
    # Simple sentence split by line breaks and punctuation
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    out = []
    for s in sentences:
        if OBLIG_HINT.search(s or "") and len(s) > 10:
            out.append(s.strip())
    return out[:12]


def classify_topic(heading: str | None, text: str) -> str | None:
    blob = (heading or "") + "\n" + (text or "")
    blob_l = blob.lower()
    best = None
    for topic, kws in TOPIC_KEYWORDS.items():
        for kw in kws:
            if kw in blob_l:
                best = topic
                break
        if best:
            break
    return best


def enrich_clause(c: Dict[str, Any]) -> Dict[str, Any]:
    text = c.get("text", "")
    heading = c.get("heading")
    ie = {
        "parties": extract_parties(text, heading),
        "amounts": extract_amounts(text),
        "durations": extract_durations(text),
        "dates": extract_dates(text),
        "references": extract_references(text),
        "obligations": extract_obligations(text),
        "topic": classify_topic(heading, text),
    }
    # Attach under "ie" namespace to avoid collisions
    out = dict(c)
    out["ie"] = ie
    return out


def run(input_json: Path, output_json: Path) -> None:
    with input_json.open("r", encoding="utf-8") as f:
        clauses = json.load(f)
    enriched = [enrich_clause(c) for c in clauses]
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    print(f"✅ Wrote {len(enriched)} enriched clauses to {output_json}")


def main():
    here = Path(__file__).resolve().parent
    default_in = here / "contract_parsed.json"
    default_out = here / "contract_ie.json"

    p = argparse.ArgumentParser(description="Enrich clause JSON with simple IE fields")
    p.add_argument("--input", "--in", dest="input", default=str(default_in), help=f"Input JSON (default: {default_in})")
    p.add_argument("--output", "--out", dest="output", default=str(default_out), help=f"Output JSON (default: {default_out})")
    args = p.parse_args()

    run(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()

