import { useEffect, useRef, useState } from "react"
import { useRagStore } from "../store/useRagStore"
import type { RagRetrievalItem } from "../types/rag"
import { Search, Quote, Copy, Check, Tag } from "./icons"

export default function SourceInspector() {
  const retrieval = useRagStore((s) => s.currentRetrieval)
  const highlightedCitationId = useRagStore((s) => s.highlightedCitationId)

  const isEmpty = retrieval.length === 0

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-2 border-b border-surface-800 px-4 py-3">
        <Search className="h-4 w-4 text-glow-400" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-slate-100">Source Inspector</h2>
        {!isEmpty && (
          <span className="ml-auto rounded-full bg-surface-800 px-2 py-0.5 text-xs text-slate-400">
            {retrieval.length} chunks
          </span>
        )}
      </header>

      {/* Announce highlight changes for screen readers. */}
      <div className="sr-only" aria-live="polite">
        {highlightedCitationId
          ? `Showing source for citation ${highlightedCitationId}`
          : ""}
      </div>

      {isEmpty ? (
        <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
          <Search className="mb-3 h-8 w-8 text-slate-600" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-300">No sources yet</p>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">
            Ask a question and the retrieved evidence chunks will appear here.
            Citations in the answer become clickable.
          </p>
        </div>
      ) : (
        <ul className="flex-1 space-y-3 overflow-y-auto p-3" aria-label="Retrieved source chunks">
          {retrieval.map((item) => (
            <ChunkCard
              key={`${item.citation_id}-${item.chunk_name}`}
              item={item}
              highlighted={item.citation_id === highlightedCitationId}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function ChunkCard({
  item,
  highlighted,
}: {
  item: RagRetrievalItem
  highlighted: boolean
}) {
  const ref = useRef<HTMLLIElement>(null)
  const [copied, setCopied] = useState(false)
  // `flash` drives the 600ms highlight animation when this chunk is targeted.
  const [flash, setFlash] = useState(false)

  useEffect(() => {
    if (!highlighted) return
    ref.current?.scrollIntoView({ behavior: "smooth", block: "center" })
    setFlash(true)
    const t = window.setTimeout(() => setFlash(false), 600)
    return () => window.clearTimeout(t)
  }, [highlighted])

  const copyQuote = async () => {
    // Copied text includes citation id + source for traceable pasting.
    const payload = `"${item.text}"\n\n— ${item.source_document} ${item.citation_id} (${item.chunk_name})`
    try {
      await navigator.clipboard.writeText(payload)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard may be unavailable (e.g. insecure context); fail silently.
    }
  }

  const labels = item.query_labels
    ? item.query_labels.split(",").map((l) => l.trim()).filter(Boolean)
    : []

  return (
    <li
      ref={ref}
      className={[
        "rounded-xl border bg-surface-850 p-3 transition-shadow",
        highlighted ? "border-glow-500/60 shadow-glow" : "border-surface-700",
        flash ? "animate-flash-highlight" : "",
      ].join(" ")}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="rounded-md border border-glow-500/40 bg-glow-500/10 px-1.5 text-xs font-medium text-glow-300">
            {item.citation_id}
          </span>
          <span className="text-xs font-medium text-slate-300">
            {Math.round(item.boosted_percentage)}% match
          </span>
        </div>
        <button
          type="button"
          onClick={copyQuote}
          aria-label="Copy quote with citation"
          className="inline-flex items-center gap-1 rounded-md border border-surface-700 px-1.5 py-1 text-xs text-slate-400 transition-colors hover:border-glow-500/50 hover:text-slate-200"
        >
          {copied ? (
            <Check className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
          ) : (
            <Copy className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          {copied ? "Copied" : "Quote"}
        </button>
      </div>

      {/* Similarity score bar */}
      <div
        className="mb-2 h-1 w-full overflow-hidden rounded-full bg-surface-700"
        role="meter"
        aria-valuenow={Math.round(item.similarity_score * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Similarity score"
      >
        <div
          className="h-full rounded-full bg-glow-500"
          style={{ width: `${Math.min(100, Math.max(0, item.similarity_score * 100))}%` }}
        />
      </div>

      <div className="max-h-44 overflow-y-auto rounded-lg bg-surface-900 p-2.5">
        <p className="flex gap-1.5 text-xs leading-relaxed text-slate-300">
          <Quote className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-600" aria-hidden="true" />
          <span>{item.text}</span>
        </p>
      </div>

      <div className="mt-2 space-y-1.5">
        <p className="truncate text-[11px] text-slate-500" title={item.source_document}>
          {item.source_document}
        </p>
        <p className="truncate text-[11px] text-slate-600" title={item.chunk_name}>
          {item.chunk_name}
        </p>
        {labels.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-0.5">
            {labels.map((label) => (
              <span
                key={label}
                className="inline-flex items-center gap-1 rounded-full border border-surface-700 bg-surface-800 px-2 py-0.5 text-[10px] text-slate-300"
              >
                <Tag className="h-2.5 w-2.5 text-glow-400" aria-hidden="true" />
                {label}
              </span>
            ))}
          </div>
        )}
      </div>
    </li>
  )
}
