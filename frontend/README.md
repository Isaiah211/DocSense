# DocSense Frontend

A dark, premium, 3-panel dashboard for the **DocSense** local RAG backend. Built
as a self-contained SPA — it does **not** modify or depend on the Python backend
source; it only calls `POST /api/rag/query`.

- **Stack:** React 18 + TypeScript (strict) + Vite + Tailwind CSS v3 + Zustand + lucide-react
- **Location:** lives entirely under `frontend/`, fully separate from the backend.

## Why these choices

- **Vite (not Next.js):** DocSense is a pure client-side SPA talking to an
  already-running local FastAPI server. There is no SSR, auth, or server routes,
  so Vite gives the leanest dev experience with no server runtime to manage.
- **Zustand (not Redux / React Query):** state is small and shared across three
  sibling panels (documents, chat, inspector). Zustand gives one predictable
  store with no provider tree or prop-drilling. The backend exposes a single
  POST action, so a plain async store action fits better than a query cache.

## Prerequisites

- Node 18+
- pnpm (or npm/yarn)
- The Python backend running locally (for live mode): from the repo root,
   activate your Python environment and run `uvicorn app.main:app --reload`.
   The API defaults to `http://localhost:8000`.
- Ollama must be running with the chosen model (e.g. `mistral`) before the
   backend can answer questions.

## Install

```bash
cd frontend
pnpm install
cp .env.example .env   # then edit if your backend isn't on :8000
```

## Run — live mode (against the real backend)

```bash
# Backend running at http://localhost:8000
pnpm dev
```

Vite serves the UI at `http://localhost:3000` and forwards `/api/*` to the
backend. If `VITE_API_BASE` is set, the frontend can also call the backend
directly; if it is left blank, the dev proxy is used.

Open `http://localhost:3000` and ask a question. The frontend sends requests to
`POST /api/rag/query` and consumes the response shape from the FastAPI app.

## Run — mock mode (no backend, no Ollama)

```bash
# Option A: env flag
echo "VITE_USE_MOCK=true" >> .env && pnpm dev

# Option B: one-off
VITE_USE_MOCK=true pnpm dev
```

In mock mode the centralized API client resolves from an in-memory
`MockServer` that returns responses **exactly** matching the backend shape
(`src/mock/mock-data.json`). A `Mock` badge appears in the top bar.
Tip: questions containing "expense", "receipt", or "low confidence" return the
low-confidence sample.

## Environment variables

| Variable              | Default                 | Purpose                                              |
| --------------------- | ----------------------- | ---------------------------------------------------- |
| `VITE_API_BASE`       | `http://localhost:8000` | Backend base URL (also the dev-proxy target).        |
| `VITE_USE_MOCK`       | `false`                 | `true` runs the UI against the in-memory mock server.|
| `VITE_API_TIMEOUT_MS` | `60000`                 | Per-request timeout for the API client.              |

If you prefer the dev proxy path, you can leave `VITE_API_BASE` blank in your
local `.env` and the browser will call `/api/rag/query` through Vite.

## Tests

```bash
pnpm test        # run once
pnpm test:watch  # watch mode
```

Vitest + React Testing Library are used (Vitest shares Jest's API/matchers and
integrates natively with Vite). See
`src/components/__tests__/CitationBadge.test.tsx` for the citation-click →
highlight example.

## Keyboard shortcuts & accessibility

- **Enter** sends a question; **Shift+Enter** inserts a newline.
- **Escape** closes the mobile drawers.
- All interactive elements have visible focus rings, ARIA labels/roles, and
  hover/focus/active/disabled states.
- Chat updates use `aria-live="polite"`; citation highlighting is announced via
  an `aria-live` region in the inspector.
- Honors `prefers-reduced-motion`.

## Project structure

```
frontend/
├─ index.html
├─ tailwind.config.js        # dark mode + surface/glow tokens + animations
├─ postcss.config.js
├─ vite.config.ts            # dev proxy + vitest config
└─ src/
   ├─ main.tsx / App.tsx
   ├─ index.css              # Tailwind + glow/animation utilities
   ├─ types/rag.ts           # exact backend response types
   ├─ api/apiClient.ts       # centralized fetch wrapper (timeout + retries)
   ├─ mock/                  # mockServer.ts + mock-data.json
   ├─ store/useRagStore.ts   # Zustand store (documents, chat, retrieval…)
   └─ components/
      ├─ AppShell.tsx        # responsive 3-panel layout
      ├─ DocumentManager.tsx # left aside
      ├─ ChatMain.tsx        # center main + composer
      ├─ SourceInspector.tsx # right aside
      ├─ MessageBubble.tsx   # renders inline [n] citation tokens
      ├─ CitationBadge.tsx   # clickable citation token
      ├─ ToastViewport.tsx   # non-blocking error/retry toasts
      └─ icons.ts            # single lucide-react icon index
```

## Backend contract (unchanged)

Request → `POST /api/rag/query`:

```json
{ "question": "…", "model": "mistral", "top_k": 3 }
```

The response shape is consumed verbatim (see `src/types/rag.ts`). **No backend
changes are required** for this frontend. The backend only needs to be running
locally before you query the UI.

## QA checklist (run locally)

1. **Upload → status:** drop a `.txt` in the left panel → row shows
   `Processing` then `Ready`.
2. **Query → answer:** ask a question → skeleton/typing indicator → grounded
   answer with `[n]` badges.
3. **Citation highlight:** click an `[n]` badge → right panel opens, scrolls to
   the matching chunk, and flashes it (~600ms).
4. **Low confidence:** in mock mode ask about "expenses" → bubble shows the
   amber low-confidence accent, disclaimer, and a "Retry with more context"
   button.
5. **Copy quote:** click `Quote` on a chunk → clipboard contains the text plus
   citation id + source document.
6. **Empty retrieval:** if `retrieval` is empty, the inspector shows an empty
   state and citation badges are disabled.
7. **Error handling:** stop the backend and ask a question → non-blocking toast
   with a working **Retry**; the UI does not crash.
8. **Responsive:** shrink the viewport → left/right asides become overlay
   drawers toggled from the top bar; **Escape** closes them.

## TODO — integrating with the real backend

- [ ] Confirm backend reachable at `VITE_API_BASE` and Ollama model is pulled.
- [ ] Wire real document upload/ingestion endpoints if/when the backend exposes
      them (today the left panel is an optimistic local simulation — no backend
      change is assumed or required).
- [ ] Optionally surface `confidence.thresholds` in a settings popover.
- [ ] Add more component tests (SourceInspector flash, MessageBubble parsing).
```
