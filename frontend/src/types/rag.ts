// Type definitions that mirror the backend response EXACTLY.
// Keys are taken verbatim from POST /api/rag/query — do not rename them.

/** Request body for POST /api/rag/query */
export interface RagQueryRequest {
  question: string
  model: string
  top_k: number
}

/** A single citation entry (subset of a retrieval item, without `text`). */
export interface RagCitation {
  citation_id: string
  source_document: string
  chunk_name: string
  chunk_path: string
  similarity_score: number
  boosted_percentage: number
  query_labels: string
}

/** A retrieval item — a citation plus the raw chunk text. */
export interface RagRetrievalItem extends RagCitation {
  text: string
}

/** Confidence block describing how trustworthy the answer is. */
export interface RagConfidence {
  level: "high" | "medium" | "low"
  top_similarity: number
  similarity_margin: number
  is_low_confidence: boolean
  thresholds: {
    top_similarity: number
    similarity_margin: number
  }
}

/** Full response shape from POST /api/rag/query. */
export interface RagQueryResponse {
  query: string
  // `model` and `top_k` are echoed back by app/main.py.
  model?: string
  top_k?: number
  answer: string
  citations: RagCitation[]
  confidence: RagConfidence
  fallback: string
  retrieval: RagRetrievalItem[]
}

// ---------------------------------------------------------------------------
// UI-only models (not part of the backend contract).
// ---------------------------------------------------------------------------

export type DocumentStatus = "Ready" | "Chunked" | "Processing"

export interface DocItem {
  id: string
  filename: string
  status: DocumentStatus
}

export type MessageRole = "user" | "assistant"

export interface ChatMessage {
  id: string
  role: MessageRole
  /** Raw text. Assistant messages may contain inline tokens like `[1]`. */
  content: string
  /** Present only while an assistant message is awaiting a response. */
  pending?: boolean
  /** Citations attached to an assistant message. */
  citations?: RagCitation[]
  confidence?: RagConfidence
  fallback?: string
  /** The original question, kept so we can offer a "retry with higher top_k". */
  sourceQuestion?: string
  /** top_k used to produce this message (for retry escalation). */
  topK?: number
  /** Retrieved source chunks for this message. */
  retrieval?: RagRetrievalItem[]
}
