import type { RagQueryRequest, RagQueryResponse } from "../types/rag"
import mockData from "./mock-data.json"

// MockServer simulates POST /api/rag/query without a backend or Ollama.
// It returns responses that EXACTLY match the real backend shape so the UI can
// be developed and tested in isolation. Toggle via VITE_USE_MOCK=true.

const HIGH = mockData.highConfidence as unknown as RagQueryResponse
const LOW = mockData.lowConfidence as unknown as RagQueryResponse

function pickMock(question: string): RagQueryResponse {
  // Any question containing these hints returns the low-confidence sample,
  // making the low-confidence flow trivial to demo.
  const q = question.toLowerCase()
  if (q.includes("expense") || q.includes("receipt") || q.includes("low confidence")) {
    return { ...LOW, query: question }
  }
  return { ...HIGH, query: question }
}

/** Resolve after `ms`, simulating network + model latency. */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function mockQueryRag(req: RagQueryRequest): Promise<RagQueryResponse> {
  // Simulate realistic latency so skeleton/typing states are visible.
  await delay(900)
  const base = pickMock(req.question)
  // Echo the requested model/top_k like the real backend does.
  return { ...base, model: req.model, top_k: req.top_k }
}
