import { useRagStore } from "../store/useRagStore"
import { AlertTriangle, RotateCw, X } from "./icons"

/**
 * Non-blocking toast stack (bottom-right). Used for backend failures with an
 * optional retry action. Announced politely to assistive tech.
 */
export default function ToastViewport() {
  const toasts = useRagStore((s) => s.toasts)
  const dismissToast = useRagStore((s) => s.dismissToast)

  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          className="pointer-events-auto flex animate-fade-in items-start gap-3 rounded-xl border border-surface-700 bg-surface-850/95 p-3 shadow-glow-sm backdrop-blur"
        >
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" aria-hidden="true" />
          <p className="flex-1 text-sm leading-relaxed text-slate-200">{t.message}</p>
          <div className="flex items-center gap-1">
            {t.actionLabel && t.onAction && (
              <button
                type="button"
                onClick={() => {
                  t.onAction?.()
                  dismissToast(t.id)
                }}
                className="inline-flex items-center gap-1 rounded-md bg-glow-600 px-2 py-1 text-xs font-medium text-slate-50 transition-colors hover:bg-glow-500 active:bg-glow-600"
              >
                <RotateCw className="h-3.5 w-3.5" aria-hidden="true" />
                {t.actionLabel}
              </button>
            )}
            <button
              type="button"
              onClick={() => dismissToast(t.id)}
              aria-label="Dismiss notification"
              className="rounded-md p-1 text-slate-400 transition-colors hover:bg-surface-700 hover:text-slate-200"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
