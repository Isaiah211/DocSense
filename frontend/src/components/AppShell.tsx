import { useEffect } from "react"
import { useRagStore } from "../store/useRagStore"
import { isMockMode } from "../api/apiClient"
import DocumentManager from "./DocumentManager"
import ChatMain from "./ChatMain"
import SourceInspector from "./SourceInspector"
import ToastViewport from "./ToastViewport"
import {
  Sparkles,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
} from "./icons"

/**
 * AppShell — responsive 3-panel dashboard.
 * - Mobile: panels are off-canvas drawers (overlay) toggled from the top bar.
 * - Desktop (lg+): left/right asides dock inline and collapse to free space.
 */
export default function AppShell() {
  const leftOpen = useRagStore((s) => s.leftOpen)
  const rightOpen = useRagStore((s) => s.rightOpen)
  const setLeftOpen = useRagStore((s) => s.setLeftOpen)
  const setRightOpen = useRagStore((s) => s.setRightOpen)

  // Close drawers on Escape (mobile usability + accessibility).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setLeftOpen(false)
        setRightOpen(false)
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [setLeftOpen, setRightOpen])

  return (
    <div className="flex h-full flex-col bg-surface-950 text-slate-200">
      <TopBar />

      <div className="relative flex min-h-0 flex-1">
        {/* Backdrop for mobile drawers */}
        {(leftOpen || rightOpen) && (
          <button
            type="button"
            aria-label="Close panels"
            onClick={() => {
              setLeftOpen(false)
              setRightOpen(false)
            }}
            className="absolute inset-0 z-20 bg-surface-950/70 backdrop-blur-sm lg:hidden"
          />
        )}

        {/* Left aside — Document management */}
        <aside
          aria-label="Document management"
          className={[
            "z-30 w-72 shrink-0 border-r border-surface-800 bg-surface-900 transition-transform duration-200",
            "absolute inset-y-0 left-0 lg:relative lg:translate-x-0",
            leftOpen ? "translate-x-0" : "-translate-x-full",
            leftOpen ? "lg:block" : "lg:hidden",
          ].join(" ")}
        >
          <DocumentManager />
        </aside>

        {/* Center main */}
        <ChatMain />

        {/* Right aside — Source inspector */}
        <aside
          aria-label="Source chunk inspector"
          className={[
            "z-30 w-80 shrink-0 border-l border-surface-800 bg-surface-900 transition-transform duration-200",
            "absolute inset-y-0 right-0 lg:relative lg:translate-x-0",
            rightOpen ? "translate-x-0" : "translate-x-full",
            rightOpen ? "lg:block" : "lg:hidden",
          ].join(" ")}
        >
          <SourceInspector />
        </aside>
      </div>

      <ToastViewport />
    </div>
  )
}

function TopBar() {
  const leftOpen = useRagStore((s) => s.leftOpen)
  const rightOpen = useRagStore((s) => s.rightOpen)
  const setLeftOpen = useRagStore((s) => s.setLeftOpen)
  const setRightOpen = useRagStore((s) => s.setRightOpen)

  return (
    <header className="flex items-center gap-3 border-b border-surface-800 bg-surface-900/80 px-3 py-2 backdrop-blur">
      <button
        type="button"
        onClick={() => setLeftOpen(!leftOpen)}
        aria-label={leftOpen ? "Collapse document panel" : "Open document panel"}
        aria-pressed={leftOpen}
        className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-surface-800 hover:text-slate-100"
      >
        {leftOpen ? (
          <PanelLeftClose className="h-5 w-5" aria-hidden="true" />
        ) : (
          <PanelLeftOpen className="h-5 w-5" aria-hidden="true" />
        )}
      </button>

      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-glow-400" aria-hidden="true" />
        <span className="text-sm font-semibold tracking-tight text-slate-100">
          DocSense
        </span>
        {isMockMode && (
          <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-300">
            Mock
          </span>
        )}
      </div>

      <button
        type="button"
        onClick={() => setRightOpen(!rightOpen)}
        aria-label={rightOpen ? "Collapse source panel" : "Open source panel"}
        aria-pressed={rightOpen}
        className="ml-auto rounded-lg p-2 text-slate-400 transition-colors hover:bg-surface-800 hover:text-slate-100"
      >
        {rightOpen ? (
          <PanelRightClose className="h-5 w-5" aria-hidden="true" />
        ) : (
          <PanelRightOpen className="h-5 w-5" aria-hidden="true" />
        )}
      </button>
    </header>
  )
}
