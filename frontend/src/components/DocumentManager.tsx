import { useRef, useState } from "react"
import { useRagStore } from "../store/useRagStore"
import type { DocItem, DocumentStatus } from "../types/rag"
import {
  FileText,
  UploadCloud,
  MoreVertical,
  Pencil,
  Trash2,
  RotateCw,
} from "./icons"

const STATUS_STYLES: Record<DocumentStatus, string> = {
  Ready: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  Chunked: "border-glow-500/30 bg-glow-500/10 text-glow-300",
  Processing: "border-amber-500/30 bg-amber-500/10 text-amber-300",
}

function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span
      className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  )
}

export default function DocumentManager() {
  const documents = useRagStore((s) => s.documents)
  const selectedDocId = useRagStore((s) => s.selectedDocId)
  const selectDocument = useRagStore((s) => s.selectDocument)
  const addDocuments = useRagStore((s) => s.addDocuments)
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragActive, setDragActive] = useState(false)

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return
    // Only accept plain-text files
    const txtFiles = Array.from(fileList).filter((f) => f.name.endsWith(".txt"))
    const rejected = fileList.length - txtFiles.length
    if (rejected > 0) {
      useRagStore.getState().pushToast({
        message: `${rejected} file(s) skipped — only .txt files are supported.`,
      })
    }
    if (txtFiles.length > 0) void addDocuments(txtFiles)
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-2 border-b border-surface-800 px-4 py-3">
        <FileText className="h-4 w-4 text-glow-400" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-slate-100">Documents</h2>
        <span className="ml-auto rounded-full bg-surface-800 px-2 py-0.5 text-xs text-slate-400">
          {documents.length}
        </span>
      </header>

      {/* Drag & drop + click-to-upload */}
      <div className="p-3">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragActive(true)
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragActive(false)
            handleFiles(e.dataTransfer.files)
          }}
          aria-label="Upload .txt documents by clicking or dropping files"
          className={[
            "flex w-full flex-col items-center gap-2 rounded-xl border border-dashed px-4 py-6 text-center transition-colors",
            dragActive
              ? "border-glow-400 bg-glow-500/10"
              : "border-surface-700 bg-surface-850 hover:border-glow-500/50",
          ].join(" ")}
        >
          <UploadCloud className="h-6 w-6 text-glow-400" aria-hidden="true" />
          <span className="text-xs font-medium text-slate-300">
            Drop .txt files or click to upload
          </span>
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".txt"
          multiple
          className="sr-only"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {/* Document list */}
      <ul className="flex-1 space-y-1 overflow-y-auto px-2 pb-3" aria-label="Uploaded documents">
        {documents.map((doc) => (
          <DocumentRow
            key={doc.id}
            doc={doc}
            selected={doc.id === selectedDocId}
            onSelect={() => selectDocument(doc.id)}
          />
        ))}
        {documents.length === 0 && (
          <li className="px-2 py-6 text-center text-xs text-slate-500">
            No documents yet. Upload a .txt file to begin.
          </li>
        )}
      </ul>
    </div>
  )
}

function DocumentRow({
  doc,
  selected,
  onSelect,
}: {
  doc: DocItem
  selected: boolean
  onSelect: () => void
}) {
  const removeDocument = useRagStore((s) => s.removeDocument)
  const renameDocument = useRagStore((s) => s.renameDocument)
  const reingestDocument = useRagStore((s) => s.reingestDocument)
  const [menuOpen, setMenuOpen] = useState(false)
  const [renaming, setRenaming] = useState(false)
  const [draft, setDraft] = useState(doc.filename)

  const commitRename = () => {
    const next = draft.trim()
    if (next) renameDocument(doc.id, next)
    else setDraft(doc.filename)
    setRenaming(false)
  }

  return (
    <li className="relative">
      <div
        className={[
          "flex items-center gap-2 rounded-lg border px-2.5 py-2 transition-colors",
          selected
            ? "border-glow-500/50 bg-glow-500/10"
            : "border-transparent hover:bg-surface-850",
        ].join(" ")}
      >
        <button
          type="button"
          onClick={onSelect}
          className="flex min-w-0 flex-1 items-center gap-2 text-left"
          aria-pressed={selected}
        >
          <FileText className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
          {renaming ? (
            <input
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onBlur={commitRename}
              onKeyDown={(e) => {
                if (e.key === "Enter") commitRename()
                if (e.key === "Escape") {
                  setDraft(doc.filename)
                  setRenaming(false)
                }
              }}
              onClick={(e) => e.stopPropagation()}
              className="min-w-0 flex-1 rounded bg-surface-900 px-1.5 py-0.5 text-xs text-slate-100 focus:outline-none"
              aria-label="Rename document"
            />
          ) : (
            <span className="truncate text-xs text-slate-200" title={doc.filename}>
              {doc.filename}
            </span>
          )}
        </button>

        <StatusBadge status={doc.status} />

        <button
          type="button"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label={`Actions for ${doc.filename}`}
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          className="rounded-md p-1 text-slate-400 transition-colors hover:bg-surface-700 hover:text-slate-200"
        >
          <MoreVertical className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {menuOpen && (
        <div
          role="menu"
          className="absolute right-2 top-11 z-20 w-40 animate-fade-in overflow-hidden rounded-lg border border-surface-700 bg-surface-850 py-1 shadow-glow-sm"
          onMouseLeave={() => setMenuOpen(false)}
        >
          <MenuItem
            icon={<RotateCw className="h-3.5 w-3.5" aria-hidden="true" />}
            label="Re-ingest"
            onClick={() => {
              void reingestDocument(doc.id)
              setMenuOpen(false)
            }}
          />
          <MenuItem
            icon={<Pencil className="h-3.5 w-3.5" aria-hidden="true" />}
            label="Rename"
            onClick={() => {
              setRenaming(true)
              setMenuOpen(false)
            }}
          />
          <MenuItem
            icon={<Trash2 className="h-3.5 w-3.5" aria-hidden="true" />}
            label="Remove"
            destructive
            onClick={() => {
              void removeDocument(doc.id)
              setMenuOpen(false)
            }}
          />
        </div>
      )}
    </li>
  )
}

function MenuItem({
  icon,
  label,
  onClick,
  destructive = false,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  destructive?: boolean
}) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      className={[
        "flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs transition-colors hover:bg-surface-700",
        destructive ? "text-rose-300" : "text-slate-200",
      ].join(" ")}
    >
      {icon}
      {label}
    </button>
  )
}
