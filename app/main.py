from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_pipeline import build_rag_chain


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
