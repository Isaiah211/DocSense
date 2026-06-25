import { create } from "zustand"
import type {
  ChatMessage,
  DocItem,
  RagRetrievalItem,
} from "../types/rag"
import {
  queryRag,
  ApiError,
  fetchDocuments,
  uploadDocument,
  deleteDocument as deleteDocumentApi,
  reingestDocumentApi,
} from "../api/apiClient"

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
  selectedMessageId: string | null

  // Actions
  setLeftOpen: (open: boolean) => void
  setRightOpen: (open: boolean) => void
  selectDocument: (id: string | null) => void
  selectMessage: (id: string | null) => void
  loadDocuments: () => Promise<void>
  addDocuments: (files: File[]) => Promise<void>
  removeDocument: (id: string) => Promise<void>
  renameDocument: (id: string, filename: string) => void
  reingestDocument: (id: string) => Promise<void>

  highlightCitation: (citationId: string | null) => void
  pushToast: (toast: Omit<ToastState, "id">) => void
  dismissToast: (id: string) => void

  submitQuestion: (question: string, topKOverride?: number) => Promise<void>
}

const uid = () => Math.random().toString(36).slice(2, 10)

export const useRagStore = create<RagState>((set, get) => ({
  documents: [],
  chatHistory: [],
  currentRetrieval: [],
  highlightedCitationId: null,
  toasts: [],
  selectedMessageId: null,

  leftOpen: true,
  rightOpen: false,
  selectedDocId: null,
  isQuerying: false,
  model: "mistral",
  topK: 3,

  setLeftOpen: (open) => set({ leftOpen: open }),
  setRightOpen: (open) => set({ rightOpen: open }),
  selectDocument: (id) => set({ selectedDocId: id }),
  selectMessage: (id) => {
    const msg = get().chatHistory.find((m) => m.id === id)
    set({
      selectedMessageId: id,
      currentRetrieval: msg?.retrieval ?? [],
    })
  },

  /** Fetch the real document list from the server. Called once on app mount. */
  loadDocuments: async () => {
    try {
      const serverDocs = await fetchDocuments()
      const docs: DocItem[] = serverDocs.map((d) => ({
        id: uid(),
        filename: d.filename,
        status: d.status === "ready" ? "Ready" : "Chunked",
      }))
      set({ documents: docs })
    } catch {
      // Silently fall back to empty — a toast would be noisy on first load
    }
  },

  /** Upload files to the server; each file is chunked + embedded before moving to Ready. */
  addDocuments: async (files) => {
    // Optimistically add each file as "Processing"
    const optimistic: DocItem[] = files.map((f) => ({
      id: uid(),
      filename: f.name,
      status: "Processing",
    }))
    set((s) => ({ documents: [...optimistic, ...s.documents] }))

    await Promise.all(
      files.map(async (file, i) => {
        const tempId = optimistic[i].id
        try {
          await uploadDocument(file)
          set((s) => ({
            documents: s.documents.map((d) =>
              d.id === tempId ? { ...d, status: "Ready" } : d,
            ),
          }))
        } catch (err) {
          const msg = err instanceof ApiError ? err.message : `Failed to upload ${file.name}.`
          // Remove the optimistic entry and surface an error toast
          set((s) => ({
            documents: s.documents.filter((d) => d.id !== tempId),
          }))
          get().pushToast({ message: msg })
        }
      }),
    )
  },

  /** Delete a document from the server, then remove it from local state. */
  removeDocument: async (id) => {
    const doc = get().documents.find((d) => d.id === id)
    if (!doc) return

    // Optimistically remove from UI
    set((s) => ({
      documents: s.documents.filter((d) => d.id !== id),
      selectedDocId: s.selectedDocId === id ? null : s.selectedDocId,
    }))

    try {
      await deleteDocumentApi(doc.filename)
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : `Failed to remove ${doc.filename}.`
      // Restore the document in UI and show error
      set((s) => ({ documents: [doc, ...s.documents] }))
      get().pushToast({ message: msg })
    }
  },

  renameDocument: (id, filename) =>
    set((s) => ({
      documents: s.documents.map((d) => (d.id === id ? { ...d, filename } : d)),
    })),

  /** Re-chunk and re-embed an existing document via the server API. */
  reingestDocument: async (id) => {
    const doc = get().documents.find((d) => d.id === id)
    if (!doc) return

    set((s) => ({
      documents: s.documents.map((d) =>
        d.id === id ? { ...d, status: "Processing" } : d,
      ),
    }))

    try {
      await reingestDocumentApi(doc.filename)
      set((s) => ({
        documents: s.documents.map((d) =>
          d.id === id ? { ...d, status: "Ready" } : d,
        ),
      }))
      get().pushToast({ message: `Re-ingestion of "${doc.filename}" complete.` })
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : `Re-ingest failed for ${doc.filename}.`
      set((s) => ({
        documents: s.documents.map((d) =>
          d.id === id ? { ...d, status: "Ready" } : d,
        ),
      }))
      get().pushToast({ message: msg })
    }
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
        selectedMessageId: assistantId,
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
              retrieval: res.retrieval,
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
