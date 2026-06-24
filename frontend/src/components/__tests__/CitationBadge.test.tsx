import { describe, it, expect, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import CitationBadge from "../CitationBadge"
import { useRagStore } from "../../store/useRagStore"

// Example test covering the critical citation-click -> highlight behavior.
// Demonstrates the pattern; expand with more cases as needed.

describe("CitationBadge", () => {
  beforeEach(() => {
    // Reset the relevant store slices before each test.
    useRagStore.setState({ rightOpen: false, highlightedCitationId: null })
  })

  it("opens the inspector and highlights the matching citation on click", async () => {
    render(<CitationBadge citationId="[1]" />)
    fireEvent.click(screen.getByRole("button", { name: /citation \[1\]/i }))

    // The right panel opens immediately.
    expect(useRagStore.getState().rightOpen).toBe(true)

    // Highlight is set on the next animation frame.
    await waitFor(() =>
      expect(useRagStore.getState().highlightedCitationId).toBe("[1]"),
    )
  })

  it("does not trigger highlighting when disabled", () => {
    render(<CitationBadge citationId="[2]" disabled />)
    fireEvent.click(screen.getByRole("button", { name: /citation \[2\]/i }))

    expect(useRagStore.getState().rightOpen).toBe(false)
    expect(useRagStore.getState().highlightedCitationId).toBeNull()
  })
})
