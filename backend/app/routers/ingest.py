"""FastAPI router for indexing clause JSON into the retrievers."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..schemas import IngestRequest, IngestResponse
from ..services.ingestion import ingest as run_ingest


router = APIRouter(prefix="/ingest", tags=["ingest"])

DEFAULT_JSON = (
    Path(__file__).resolve().parents[1] / "services" / "contract_parsed.json"
)


@router.post("", response_model=IngestResponse)
def ingest(payload: IngestRequest) -> IngestResponse:
    """Trigger an ingestion run via the existing service layer."""

    json_path = Path(payload.json_path) if payload.json_path else DEFAULT_JSON
    if not json_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Clause JSON not found at '{json_path}'",
        )

    try:
        with json_path.open("r", encoding="utf-8") as f:
            clauses = json.load(f)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON payload in '{json_path}': {exc}",
        ) from exc

    clause_count = len(clauses)

    try:
        run_ingest(str(json_path), reset=payload.reset, index_name=payload.index_name)
    except Exception as exc:  # pragma: no cover - pass through to API caller
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {exc}",
        ) from exc

    return IngestResponse(
        indexed=clause_count,
        index_name=payload.index_name,
        qdrant_collection=payload.index_name,
        reset=payload.reset,
        message=f"Indexed {clause_count} clauses from {json_path.name}",
    )
