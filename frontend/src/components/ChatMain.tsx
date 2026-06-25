import { useEffect, useRef, useState } from "react"
import { useRagStore } from "../store/useRagStore"
import MessageBubble from "./MessageBubble"
import { Sparkles, Send, Layers, Receipt, Scale, ArrowDown } from "./icons"

const QUICK_ACTIONS = [
  { label: "Summarize Docs", icon: Layers, query: "Summarize the key points across my documents." },
  { label: "Find Receipts", icon: Receipt, query: "What were the company's Q3 travel expenses?" },
  { label: "Compare Answers", icon: Scale, query: "How did Mask R-CNN improve on Faster R-CNN?" },
]

export default function ChatMain() {
  const chatHistory = useRagStore((s) => s.chatHistory)
  const isQuerying = useRagStore((s) => s.isQuerying)
  const submitQuestion = useRagStore((s) => s.submitQuestion)

  const [value, setValue] = useState("")
  const [focused, setFocused] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [showJump, setShowJump] = useState(false)

  const hasMessages = chatHistory.length > 0

  // Track whether the user is pinned to the bottom. We only auto-scroll new
  // content into view when they already are (assistive focus management).
  const atBottomRef = useRef(true)
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const onScroll = () => {
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight
      atBottomRef.current = distance < 80
      setShowJump(distance >= 80)
    }
    el.addEventListener("scroll", onScroll)
    return () => el.removeEventListener("scroll", onScroll)
  }, [])

  useEffect(() => {
    if (atBottomRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
    }
  }, [chatHistory])

  const send = () => {
    const q = value.trim()
    if (!q || isQuerying) return
    submitQuestion(q)
    setValue("")
    // Collapse the textarea back to single-line after sending.
    if (textareaRef.current) textareaRef.current.style.height = "auto"
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter submits; Shift+Enter inserts a newline.
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const autoGrow = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const el = e.currentTarget
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  const useExample = (q: string) => {
    setValue(q)
    textareaRef.current?.focus()
  }

  return (
    <main className="relative flex min-w-0 flex-1 flex-col" aria-label="DocSense conversation">
      {/* Message list / empty state */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto"
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
      >
        {hasMessages ? (
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-6">
            {chatHistory.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            <div ref={bottomRef} />
          </div>
        ) : (
          <EmptyState onPick={useExample} />
        )}
      </div>

      {showJump && (
        <button
          type="button"
          onClick={() => bottomRef.current?.scrollIntoView({ behavior: "smooth" })}
          aria-label="Jump to latest message"
          className="absolute bottom-28 left-1/2 -translate-x-1/2 rounded-full border border-surface-700 bg-surface-800 p-2 text-slate-200 shadow-glow-sm transition-colors hover:bg-surface-700"
        >
          <ArrowDown className="h-4 w-4" aria-hidden="true" />
        </button>
      )}

      {/* Composer */}
      <div className="border-t border-surface-800 bg-surface-900/80 p-4 backdrop-blur">
        <div className="mx-auto w-full max-w-3xl">
          <div
            className={[
              "flex items-end gap-2 rounded-2xl border bg-surface-850 p-2 transition-shadow",
              focused ? "border-glow-500/60 shadow-glow" : "border-surface-700",
            ].join(" ")}
          >
            <label htmlFor="question-input" className="sr-only">
              Ask a question about your documents
            </label>
            <textarea
              id="question-input"
              ref={textareaRef}
              rows={1}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onInput={autoGrow}
              onKeyDown={onKeyDown}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="Ask anything about your documents…  (Enter to send, Shift+Enter for newline)"
              className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm leading-relaxed text-slate-100 placeholder:text-slate-500 focus:outline-none focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:outline-none"
            />
            <button
              type="button"
              onClick={send}
              disabled={!value.trim() || isQuerying}
              aria-label="Send question"
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-glow-600 text-slate-50 transition-colors hover:bg-glow-500 active:bg-glow-600 disabled:cursor-not-allowed disabled:bg-surface-700 disabled:text-slate-500"
            >
              <Send className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}

function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="ambient-glow flex h-full flex-col items-center justify-center px-4 text-center">
      <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-glow-500/30 bg-glow-500/10 px-3 py-1 text-xs font-medium text-glow-300">
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
        Document Intelligence
      </div>
      <h1 className="text-balance text-4xl font-semibold tracking-tight text-slate-100 sm:text-5xl">
        DocSense
      </h1>
      <p className="mt-3 max-w-md text-pretty text-sm leading-relaxed text-slate-400">
        Ask natural-language questions and get grounded, citation-backed answers
        from your personal document collection.
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
        {QUICK_ACTIONS.map(({ label, icon: Icon, query }) => (
          <button
            key={label}
            type="button"
            onClick={() => onPick(query)}
            className="inline-flex items-center gap-1.5 rounded-full border border-surface-700 bg-surface-850 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:border-glow-500/50 hover:text-slate-100"
          >
            <Icon className="h-3.5 w-3.5 text-glow-400" aria-hidden="true" />
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}
