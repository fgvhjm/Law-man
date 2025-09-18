"""FastAPI router for hybrid + reranked clause search."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas import ClauseHit, HybridSearchRequest, HybridSearchResponse
from ..services.hybrid_search import hybrid_search as run_hybrid_search
from ..services.reranker import rerank as run_rerank


router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("", response_model=HybridSearchResponse)
def ask(payload: HybridSearchRequest) -> HybridSearchResponse:
    """Run hybrid retrieval (and optional reranking) for the supplied query."""

    try:
        hits = run_hybrid_search(
            payload.query, top_k=payload.top_k, alpha=payload.alpha
        )
    except Exception as exc:  # pragma: no cover - bubble up to client
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {exc}") from exc

    reranked = False
    if payload.rerank:
        try:
            hits = run_rerank(payload.query, hits, top_k=payload.top_k)
            reranked = True
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=f"Reranking failed: {exc}") from exc

    results = [ClauseHit.model_validate(hit) for hit in hits]

    return HybridSearchResponse(
        query=payload.query,
        top_k=payload.top_k,
        alpha=payload.alpha,
        reranked=reranked,
        results=results,
    )
