"""Pydantic schemas for the FastAPI layer."""

from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class IngestRequest(BaseModel):
    """Payload to trigger ingestion of clause JSON into the retrievers."""

    json_path: Optional[str] = Field(
        default=None,
        description="Path to the Docling clause JSON; defaults to services/contract_parsed.json",
    )
    index_name: str = Field(
        default="contracts",
        description="OpenSearch index / Qdrant collection name",
    )
    reset: bool = Field(
        default=True,
        description="Drop and recreate the OpenSearch index and Qdrant collection before ingesting",
    )


class IngestResponse(BaseModel):
    """Confirmation that ingestion completed."""

    indexed: int = Field(description="Number of clauses processed")
    index_name: str
    qdrant_collection: str
    reset: bool
    message: str


class HybridSearchRequest(BaseModel):
    """Query payload for the hybrid search endpoint."""

    query: str = Field(..., description="Natural language query or keywords")
    top_k: int = Field(10, ge=1, le=100, description="Number of clauses to return")
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="Hybrid weight between BM25 and vector scores")
    rerank: bool = Field(
        False,
        description="Whether to rerank the hybrid results with the cross-encoder",
    )
    summarize: bool = Field(
        False,
        description="Generate a Gemini summary based on the final (reranked) results",
    )


class ClauseHit(BaseModel):
    """Single clause hit returned from hybrid search."""

    model_config = ConfigDict(extra="allow")

    contract_id: Optional[str]
    clause_id: Optional[str]
    heading: Optional[str]
    text_snippet: str
    page: Optional[int]
    line_range: List[Optional[int]]
    lang: Optional[str]
    score: Optional[float] = None
    highlight: List[str] = Field(default_factory=list)
    bm25_score: Optional[float] = None
    vec_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    reranker_score: Optional[float] = None


class HybridSearchResponse(BaseModel):
    """Response payload for hybrid search."""

    query: str
    top_k: int
    alpha: float
    reranked: bool
    results: List[ClauseHit]
    summary: Optional[str] = Field(
        default=None,
        description="Gemini-generated summary of the retrieved clauses",
    )
