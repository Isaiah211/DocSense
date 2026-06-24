import { useRagStore } from "../store/useRagStore"

interface CitationBadgeProps {
  /** Stable id from the backend, e.g. "[1]". */
  citationId: string
  /** Disable interaction when there is no retrieval evidence to open. */
  disabled?: boolean
}

/**
 * Clickable inline citation token rendered inside assistant messages.
 * Clicking (or pressing Enter/Space) opens the Source Inspector and asks it to
 * scroll to + flash the matching chunk.
 */
export default function CitationBadge({ citationId, disabled = false }: CitationBadgeProps) {
  const setRightOpen = useRagStore((s) => s.setRightOpen)
  const highlightCitation = useRagStore((s) => s.highlightCitation)

  const activate = () => {
    if (disabled) return
    setRightOpen(true)
    // Re-trigger highlight even if it's the same id: clear then set on next frame.
    highlightCitation(null)
    requestAnimationFrame(() => highlightCitation(citationId))
  }

  return (
    <button
      type="button"
      onClick={activate}
      disabled={disabled}
      aria-label={`Open source for citation ${citationId}`}
      title={disabled ? "No source available" : `View source ${citationId}`}
      className="mx-0.5 inline-flex items-center rounded-md border border-glow-500/40 bg-glow-500/10 px-1.5 align-baseline text-xs font-medium text-glow-400 transition-colors hover:border-glow-400 hover:bg-glow-500/20 focus-visible:bg-glow-500/20 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {citationId}
    </button>
  )
}
