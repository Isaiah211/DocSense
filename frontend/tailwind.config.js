/** @type {import('tailwindcss').Config} */
export default {
  // Class-based dark mode. The app is dark-first; the <html> element carries
  // the `dark` class so all `dark:` variants resolve immediately.
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Deep-blue surface ramp used across the dashboard panels.
        surface: {
          950: "#070b18",
          900: "#0b1020",
          850: "#0f1530",
          800: "#141a3a",
          700: "#1b2350",
        },
        // Neon indigo accent used for glows, focus rings and citations.
        glow: {
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(99,102,241,0.25), 0 0 32px -8px rgba(99,102,241,0.55)",
        "glow-sm": "0 0 0 1px rgba(99,102,241,0.2), 0 0 16px -6px rgba(99,102,241,0.45)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "flash-highlight": {
          "0%": { backgroundColor: "rgba(99,102,241,0.0)" },
          "30%": { backgroundColor: "rgba(99,102,241,0.28)" },
          "100%": { backgroundColor: "rgba(99,102,241,0.0)" },
        },
        "typing-bounce": {
          "0%, 80%, 100%": { transform: "translateY(0)", opacity: "0.4" },
          "40%": { transform: "translateY(-3px)", opacity: "1" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease-out both",
        "flash-highlight": "flash-highlight 0.6s ease-out",
        "typing-bounce": "typing-bounce 1.2s infinite ease-in-out",
      },
    },
  },
  plugins: [],
}
