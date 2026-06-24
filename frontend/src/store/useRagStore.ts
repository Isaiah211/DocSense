import { create } from "zustand"
import type {
  ChatMessage,
  DocItem,
  RagRetrievalItem,
} from "../types/rag"
import { queryRag, ApiError } from "../api/apiClient"

// Why Zustand?
// The state here is small, cross-cutting, and read by sibling panels that are
// not in a parent/child relationship (left documents, center chat, right
// inspector). Zustand gives a single predictable store with zero boilerplate
// and no provider tree — simpler than Redux and avoids prop-drilling or
// context re-render churn. React Query would add value if we had lots of
// cacheable GET endpoints, but the backend exposes a single POST action, so a
// plain store with an async action is the right fit.

export interface ToastState {
  id: string
  message: string
  actionLabel?: string
  onAction?: () => void
}

interface RagState {
  // Data
  documents: DocItem[]
  chatHistory: ChatMessage[]
  currentRetrieval: RagRetrievalItem[]
  highlightedCitationId: string | null
  toasts: ToastState[]

  // UI
  leftOpen: boolean
  rightOpen: boolean
  selectedDocId: string | null
  isQuerying: boolean
  model: string
  topK: number

  // Actions
  setLeftOpen: (open: boolean) => void
  setRightOpen: (open: boolean) => void
  selectDocument: (id: string | null) => void
  addDocuments: (files: File[]) => void
  removeDocument: (id: string) => void
  renameDocument: (id: string, filename: string) => void
  reingestDocument: (id: string) => void

  highlightCitation: (citationId: string | null) => void
  pushToast: (toast: Omit<ToastState, "id">) => void
  dismissToast: (id: string) => void

  submitQuestion: (question: string, topKOverride?: number) => Promise<void>
}

const SEED_DOCS: DocItem[] = [
  { id: "doc-1", filename: "A Brief History of CNNs in Image Segmentation.txt", status: "Ready" },
  { id: "doc-2", filename: "Attention Is All You Need.txt", status: "Ready" },
  { id: "doc-3", filename: "budgeting-notes.txt", status: "Chunked" },
]

const uid = () => Math.random().toString(36).slice(2, 10)

export const useRagStore = create<RagState>((set, get) => ({
  documents: SEED_DOCS,
  chatHistory: [],
  currentRetrieval: [],
  highlightedCitationId: null,
  toasts: [],

  leftOpen: true,
  rightOpen: false,
  selectedDocId: null,
  isQuerying: false,
  model: "mistral",
  topK: 3,

  setLeftOpen: (open) => set({ leftOpen: open }),
  setRightOpen: (open) => set({ rightOpen: open }),
  selectDocument: (id) => set({ selectedDocId: id }),

  // Optimistic upload: files appear immediately as "Processing", then settle.
  addDocuments: (files) => {
    const newDocs: DocItem[] = files.map((f) => ({
      id: uid(),
      filename: f.name,
      status: "Processing",
    }))
    set((s) => ({ documents: [...newDocs, ...s.documents] }))
    // Simulate the backend chunking pipeline completing.
    newDocs.forEach((doc) => {
      window.setTimeout(() => {
        set((s) => ({
          documents: s.documents.map((d) =>
            d.id === doc.id ? { ...d, status: "Ready" } : d,
          ),
        }))
      }, 1600)
    })
    get().pushToast({ message: `Added ${files.length} document(s) for processing.` })
  },

  removeDocument: (id) =>
    set((s) => ({
      documents: s.documents.filter((d) => d.id !== id),
      selectedDocId: s.selectedDocId === id ? null : s.selectedDocId,
    })),

  renameDocument: (id, filename) =>
    set((s) => ({
      documents: s.documents.map((d) => (d.id === id ? { ...d, filename } : d)),
    })),

  // Optimistic re-ingestion: flip to "Processing" then back to "Ready".
  reingestDocument: (id) => {
    set((s) => ({
      documents: s.documents.map((d) =>
        d.id === id ? { ...d, status: "Processing" } : d,
      ),
    }))
    window.setTimeout(() => {
      set((s) => ({
        documents: s.documents.map((d) =>
          d.id === id ? { ...d, status: "Ready" } : d,
        ),
      }))
      get().pushToast({ message: "Re-ingestion complete." })
    }, 1800)
  },

  highlightCitation: (citationId) => set({ highlightedCitationId: citationId }),

  pushToast: (toast) => {
    const id = uid()
    set((s) => ({ toasts: [...s.toasts, { ...toast, id }] }))
    // Auto-dismiss after a few seconds (non-blocking).
    window.setTimeout(() => get().dismissToast(id), 6000)
  },

  dismissToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),

  submitQuestion: async (question, topKOverride) => {
    const trimmed = question.trim()
    if (!trimmed || get().isQuerying) return

    const topK = topKOverride ?? get().topK
    const userMsg: ChatMessage = { id: uid(), role: "user", content: trimmed }
    const assistantId = uid()
    const pendingMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      pending: true,
      sourceQuestion: trimmed,
      topK,
    }

    set((s) => ({
      chatHistory: [...s.chatHistory, userMsg, pendingMsg],
      isQuerying: true,
    }))

    try {
      const res = await queryRag(
        { question: trimmed, model: get().model, top_k: topK },
        { retries: 1 },
      )

      set((s) => ({
        isQuerying: false,
        currentRetrieval: res.retrieval,
        // Open inspector automatically when we have evidence to show.
        rightOpen: res.retrieval.length > 0 ? true : s.rightOpen,
        chatHistory: s.chatHistory.map((m) =>
          m.id === assistantId
            ? {
              ...m,
              pending: false,
              content: res.answer,
              citations: res.citations,
              confidence: res.confidence,
              fallback: res.fallback,
            }
            : m,
        ),
      }))
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Failed to reach the DocSense backend."
      // Remove the pending bubble; surface a retry toast instead of crashing.
      set((s) => ({
        isQuerying: false,
        chatHistory: s.chatHistory.filter((m) => m.id !== assistantId),
      }))
      get().pushToast({
        message,
        actionLabel: "Retry",
        onAction: () => get().submitQuestion(trimmed, topK),
      })
    }
  },
}))
