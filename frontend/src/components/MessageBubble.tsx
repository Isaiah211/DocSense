import type { ChatMessage } from "../types/rag"
import { useRagStore } from "../store/useRagStore"
import CitationBadge from "./CitationBadge"
import { AlertTriangle, RotateCw } from "./icons"

interface MessageBubbleProps {
  message: ChatMessage
}

// Matches inline citation tokens like "[1]" or "[12]". The capture group keeps
// the delimiter so we can render the original token text on the badge.
const CITATION_RE = /(\[\d+\])/g

/** Render assistant text, converting [n] tokens into clickable CitationBadges. */
function renderWithCitations(text: string, hasEvidence: boolean) {
  return text.split(CITATION_RE).map((part, i) => {
    if (CITATION_RE.test(part)) {
      // Reset lastIndex because the regex is global and reused via .test().
      CITATION_RE.lastIndex = 0
      return <CitationBadge key={i} citationId={part} disabled={!hasEvidence} />
    }
    return <span key={i}>{part}</span>
  })
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 animate-typing-bounce rounded-full bg-glow-400"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const submitQuestion = useRagStore((s) => s.submitQuestion)
  const isUser = message.role === "user"
  const isLowConfidence = message.confidence?.is_low_confidence === true
  const hasEvidence = (message.citations?.length ?? 0) > 0

  if (isUser) {
    return (
      <article className="flex animate-fade-in justify-end" aria-label="Your message">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-glow-600 px-4 py-2.5 text-sm leading-relaxed text-slate-50 shadow-glow-sm">
          {message.content}
        </div>
      </article>
    )
  }

  // Assistant message (pending or complete).
  const retryWithMoreContext = () =>
    submitQuestion(message.sourceQuestion ?? "", (message.topK ?? 3) + 3)

  return (
    <article className="flex animate-fade-in justify-start" aria-label="DocSense answer">
      <div
        className={[
          "max-w-[85%] rounded-2xl rounded-bl-sm border px-4 py-3 text-sm leading-relaxed",
          isLowConfidence
            ? "border-amber-500/40 bg-amber-500/5 text-slate-200"
            : "border-surface-700 bg-surface-850 text-slate-200",
        ].join(" ")}
      >
        {message.pending ? (
          <div className="flex flex-col gap-2 py-1" aria-label="DocSense is thinking">
            <TypingIndicator />
            {/* Skeleton lines while we wait for the backend. */}
            <div className="h-2.5 w-48 animate-pulse rounded bg-surface-700" />
            <div className="h-2.5 w-40 animate-pulse rounded bg-surface-700" />
            <span className="sr-only">Generating an answer, please wait.</span>
          </div>
        ) : (
          <>
            {isLowConfidence && (
              <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-amber-400">
                <AlertTriangle className="h-4 w-4" aria-hidden="true" />
                Low confidence answer
              </div>
            )}

            <div className="whitespace-pre-wrap">
              {renderWithCitations(message.content, hasEvidence)}
            </div>

            {isLowConfidence && message.fallback && (
              <p className="mt-2 border-t border-amber-500/20 pt-2 text-xs leading-relaxed text-amber-300/90">
                {message.fallback}
              </p>
            )}

            {isLowConfidence && (
              <button
                type="button"
                onClick={retryWithMoreContext}
                className="mt-2 inline-flex items-center gap-1.5 rounded-md border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-200 transition-colors hover:bg-amber-500/20"
              >
                <RotateCw className="h-3.5 w-3.5" aria-hidden="true" />
                Retry with more context
              </button>
            )}
          </>
        )}
      </div>
    </article>
  )
}
