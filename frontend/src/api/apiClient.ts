import type { RagQueryRequest, RagQueryResponse } from "../types/rag"
import { mockQueryRag } from "../mock/mockServer"

// Centralized fetch wrapper for the DocSense backend.
// - Single place to configure base URL, timeout, retries and error mapping.
// - Transparently switches to the mock server when VITE_USE_MOCK=true.

const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "")
const USE_MOCK = String(import.meta.env.VITE_USE_MOCK) === "true"
const DEFAULT_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 60000)

export class ApiError extends Error {
  status?: number
  constructor(message: string, status?: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

export interface QueryOptions {
  /** Number of automatic retries on network/timeout failure. Default 1. */
  retries?: number
  /** Per-attempt timeout in ms. Defaults to VITE_API_TIMEOUT_MS. */
  timeoutMs?: number
  /** Allow callers to cancel from the outside. */
  signal?: AbortSignal
}

/** Whether the client is currently running against the mock server. */
export const isMockMode = USE_MOCK

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number,
  externalSignal?: AbortSignal,
): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  // Chain an external abort signal (e.g. component unmount) into ours.
  if (externalSignal) {
    if (externalSignal.aborted) controller.abort()
    else externalSignal.addEventListener("abort", () => controller.abort(), { once: true })
  }
  try {
    return await fetch(url, { ...init, signal: controller.signal })
  } finally {
    clearTimeout(timer)
  }
}

/**
 * Send a question to POST /api/rag/query.
 * Handles timeouts and a configurable number of retries. In mock mode it
 * resolves from the in-memory MockServer instead of hitting the network.
 */
export async function queryRag(
  body: RagQueryRequest,
  options: QueryOptions = {},
): Promise<RagQueryResponse> {
  if (USE_MOCK) {
    return mockQueryRag(body)
  }

  const { retries = 1, timeoutMs = DEFAULT_TIMEOUT, signal } = options
  const url = `${API_BASE}/api/rag/query`

  let lastError: unknown
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetchWithTimeout(
        url,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
        timeoutMs,
        signal,
      )

      if (!res.ok) {
        let detail = `Request failed with status ${res.status}`
        try {
          const data = (await res.json()) as { detail?: string }
          if (data?.detail) detail = data.detail
        } catch {
          // Non-JSON error body — keep the generic message.
        }
        // 4xx errors are not retried; they will not succeed on retry.
        if (res.status >= 400 && res.status < 500) {
          throw new ApiError(detail, res.status)
        }
        lastError = new ApiError(detail, res.status)
        continue
      }

      return (await res.json()) as RagQueryResponse
    } catch (err) {
      if (err instanceof ApiError && err.status && err.status < 500) {
        throw err // client error — surface immediately
      }
      lastError = err
      // Brief backoff before the next attempt.
      if (attempt < retries) await new Promise((r) => setTimeout(r, 400 * (attempt + 1)))
    }
  }

  if (lastError instanceof DOMException && lastError.name === "AbortError") {
    throw new ApiError("The request timed out. Please try again.")
  }
  throw lastError instanceof Error
    ? new ApiError(lastError.message)
    : new ApiError("Unknown error contacting the DocSense backend.")
}
