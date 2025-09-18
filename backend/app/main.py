"""FastAPI application wiring the ingestion and search routers."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import ask as ask_router
from .routers import ingest as ingest_router


app = FastAPI(title="LawMan API", version="0.1.0")

# Allow local tools / frontends to call the API without CORS issues during dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Simple readiness probe."""

    return {"status": "ok"}


app.include_router(ingest_router.router)
app.include_router(ask_router.router)


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
