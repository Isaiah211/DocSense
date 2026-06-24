import { defineConfig } from "vitest/config"
import react from "@vitejs/plugin-react"

// Vite is used instead of Next.js because DocSense is a pure client-side SPA
// that talks to an already-running local Python (FastAPI) backend. There is no
// SSR, no auth, and no server routes needed — so Vite gives the fastest, leanest
// dev experience with zero server runtime to manage.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    // Dev proxy: forward /api/* to the local FastAPI backend so the browser
    // never hits CORS issues during development. Override the target with
    // VITE_API_BASE if your backend runs elsewhere.
    proxy: {
      "/api": {
        target: process.env.VITE_API_BASE || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
})
