import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_pipeline import build_rag_chain
from .ingest import ingest_files, list_documents, remove_document

RAW_DIR = "data"


class RagQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question to answer from the document corpus")
    model: str = Field(default="mistral", description="Local Ollama model name")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of retrieved chunks to send to the model")


class RagCitation(BaseModel):
    citation_id: str
    source_document: str
    chunk_name: str
    chunk_path: str
    similarity_score: float
    boosted_percentage: float
    query_labels: str


class RagConfidence(BaseModel):
    level: str
    top_similarity: float
    similarity_margin: float
    is_low_confidence: bool
    thresholds: Dict[str, float]


class RagQueryResponse(BaseModel):
    question: str
    model: str
    top_k: int
    answer: str
    citations: List[RagCitation]
    confidence: RagConfidence
    fallback: str
    retrieval: List[Dict[str, Any]]


app = FastAPI(
    title="DocSense RAG API",
    version="1.0.0",
    description="Frontend-ready API for the DocSense retrieval-augmented generation pipeline.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=8)
def _get_chain(model_name: str, top_k: int):
    return build_rag_chain(model_name=model_name, top_k=top_k)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/rag/query", response_model=RagQueryResponse)
def query_rag(request: RagQueryRequest) -> RagQueryResponse:
    try:
        chain = _get_chain(request.model, request.top_k)
        response = chain.invoke({"input": request.question})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG request failed: {exc}") from exc

    return RagQueryResponse(
        question=response["query"],
        model=request.model,
        top_k=request.top_k,
        answer=response["answer"],
        citations=response["citations"],
        confidence=response["confidence"],
        fallback=response.get("fallback", ""),
        retrieval=response["retrieval"],
    )


# ---------------------------------------------------------------------------
# Document management endpoints
# ---------------------------------------------------------------------------

@app.get("/api/documents")
def get_documents() -> List[Dict[str, Any]]:
    """List all .txt source documents and their index status."""
    return list_documents()


@app.post("/api/documents/upload", status_code=201)
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a .txt file, chunk and embed it, then reload the search index."""
    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported.")

    dest = os.path.join(RAW_DIR, file.filename)
    if os.path.exists(dest):
        raise HTTPException(
            status_code=409,
            detail=f"A document named '{file.filename}' already exists. Remove it first or rename the file.",
        )

    os.makedirs(RAW_DIR, exist_ok=True)
    content = await file.read()
    with open(dest, "wb") as out_f:
        out_f.write(content)

    try:
        result = ingest_files([file.filename])
    except Exception as exc:
        # If ingestion fails, clean up the saved file
        if os.path.exists(dest):
            os.remove(dest)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return {
        "filename": file.filename,
        "status": "ready",
        "processed": result["processed"],
        "skipped": result["skipped"],
    }


@app.delete("/api/documents/{filename}", status_code=200)
def delete_document(filename: str) -> Dict[str, Any]:
    """Remove a document, delete its chunks, and rebuild the search index."""
    try:
        removed = remove_document(filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Removal failed: {exc}") from exc

    if not removed:
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")

    return {"filename": filename, "status": "removed"}


@app.post("/api/documents/{filename}/reingest", status_code=200)
def reingest_document(filename: str) -> Dict[str, Any]:
    """Force re-chunk and re-embed an existing document (e.g. after manual edits)."""
    file_path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")

    # Touch the file so the mtime check in ingest_files forces reprocessing.
    import time
    os.utime(file_path, (time.time(), time.time()))

    try:
        result = ingest_files([filename])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Re-ingestion failed: {exc}") from exc

    return {
        "filename": filename,
        "status": "ready",
        "processed": result["processed"],
        "skipped": result["skipped"],
    }
