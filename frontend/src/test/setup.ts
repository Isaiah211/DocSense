import "@testing-library/jest-dom"

// Vitest is used (not Jest) because the project builds with Vite. Vitest shares
// Jest's API and matchers via @testing-library/jest-dom, so the tests below
// read identically to Jest + RTL tests. requestAnimationFrame is polyfilled for
// jsdom so CitationBadge's deferred highlight works under test.
if (typeof globalThis.requestAnimationFrame === "undefined") {
  globalThis.requestAnimationFrame = (cb: FrameRequestCallback) =>
    setTimeout(() => cb(Date.now()), 0) as unknown as number
}
