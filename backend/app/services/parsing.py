#!/usr/bin/env python3
"""
PDF → Docling → Clauses → Page + Line Anchors → JSON Records
"""

# ---------- Imports ----------
import argparse
import io
import pathlib
import re
from typing import Dict, List

# Docling
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# PDF page-level text extraction
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer


# ---------- Step 1: Run Docling ----------
def run_docling(pdf_path: str):
    """
    Use Docling to parse PDF into Markdown (with OCR + tables enabled).
    """
    pipeline = PdfPipelineOptions(
        do_ocr=True,
        ocr_options=TesseractCliOcrOptions(lang=["auto"]),  # auto language detection
        do_table_structure=True                             # preserve tables in MD
    )

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline)}
    )

    result = converter.convert(pdf_path).document
    md = result.export_to_markdown()
    return md


# ---------- Step 2: Split Markdown into Clauses ----------
H_MD = re.compile(r'^#{1,6}\s+(.*)')       # markdown headings
H_NUM = re.compile(r'^(\d+(?:\.\d+)*)\s+(.*)')  # numbered headings

def split_into_clauses(md: str) -> List[Dict]:
    """
    Convert markdown text into clause dictionaries with text + heading.
    """
    clauses, buf, heading, sec = [], [], None, None

    def flush():
        nonlocal buf, heading, sec
        if buf:
            clauses.append({
                "heading": heading or None,
                "section_number": sec,
                "text": "\n".join(buf).strip()
            })
            buf.clear()

    for ln in (l.strip() for l in md.splitlines() if l.strip()):
        m1, m2 = H_MD.match(ln), H_NUM.match(ln)
        is_caps = len(ln) < 120 and ln.isupper()

        if m1 or m2 or is_caps:
            flush()
            heading = m1.group(1) if m1 else (m2.group(2) if m2 else ln)
            sec = m2.group(1) if m2 else None
            buf.append(heading)
        else:
            buf.append(ln)

    flush()
    return clauses


# ---------- Step 3: Extract Page-Level Text ----------
def extract_page_texts(pdf_path: str) -> List[str]:
    """
    Get plain text per page (for alignment).
    """
    page_texts = []
    for layout in extract_pages(pdf_path):
        parts = []
        for el in layout:
            if isinstance(el, LTTextContainer):
                parts.append(el.get_text())
        page_texts.append("\n".join(parts))
    return page_texts


# ---------- Step 4: Best Page + Line Alignment ----------
def best_page_for_clause(clause_text: str, pages_text: List[str]) -> int | None:
    """
    Decide the most likely page for a clause by overlap of tokens.
    """
    if not pages_text:
        return None

    snippet = clause_text[:300]  # short context window
    tokens = re.findall(r"\w{5,}", snippet)  # words with ≥5 chars
    best_i, best_score = None, -1

    for i, pg in enumerate(pages_text):
        score = sum(1 for tok in tokens if tok in pg)
        if score > best_score:
            best_score, best_i = score, i

    return (best_i + 1) if best_i is not None else None


def line_span_on_page(clause_text: str, page_text: str) -> tuple[int, int]:
    """
    Find start + end line numbers for a clause inside a page.
    """
    snippet = clause_text[:200]
    idx = page_text.find(snippet)

    if idx == -1:
        first_line = next((l for l in clause_text.splitlines() if l.strip()), "")
        idx = page_text.find(first_line) if first_line else -1

    if idx == -1:
        start = 1
    else:
        start = page_text[:idx].count("\n") + 1

    end = start + clause_text.count("\n")
    return start, end


# ---------- Step 5: Pack into Final Records ----------
def to_records(clauses_basic, filename: str, pages_text: List[str] | None):
    """
    Combine clause info + page alignment into structured records.
    """
    records = []
    for i, c in enumerate(clauses_basic, start=1):
        # Guess page number
        page = c.get("page")
        if pages_text and not page:
            page = best_page_for_clause(c["text"], pages_text)

        # Line span within page
        if pages_text and page:
            ls, le = line_span_on_page(c["text"], pages_text[page - 1])
        else:
            ls, le = 1, 1 + c["text"].count("\n")

        records.append({
            "contract_id": filename,
            "clause_id": f"c{i}",
            "heading": c.get("heading") or f"Clause {i}",
            "text": c["text"],
            "page": page if page else None,
            "line_start": ls,
            "line_end": le,
            "lang": "en"
        })
    return records


# ---------- Main Runner ----------
if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent
    repo_root = here.parent.parent.parent
    default_pdf = repo_root / "contract.pdf"
    default_output = here / "contract_parsed.json"

    parser = argparse.ArgumentParser(description="Parse a contract PDF into clause JSON")
    parser.add_argument(
        "--pdf",
        dest="pdf_path",
        default=str(default_pdf),
        help=f"Path to the contract PDF (default: {default_pdf})",
    )
    parser.add_argument(
        "--out",
        dest="output_json",
        default=str(default_output),
        help=f"Destination for the clause JSON (default: {default_output})",
    )
    args = parser.parse_args()

    pdf_path = pathlib.Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found at {pdf_path}")

    output_path = pathlib.Path(args.output_json).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    filename = pdf_path.name

    # Step 1: Docling Markdown
    md = run_docling(str(pdf_path))

    # Step 2: Split into clauses
    clauses_basic = split_into_clauses(md)

    # Step 3: Extract page texts
    pages_text = extract_page_texts(str(pdf_path))

    # Step 4 + 5: Build records
    records = to_records(clauses_basic, filename, pages_text)

    # Preview
    import json

    print(json.dumps(records[:5], indent=2))

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"Saved {len(records)} clauses to {output_path}")
