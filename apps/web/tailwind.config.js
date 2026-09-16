/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14130F",
        "ink-soft": "#3C392F",
        "ink-softer": "#4A463B",
        "ink-line": "#2C2A23",
        "ink-line-2": "#3B3930",
        "ink-raised": "#191811",
        muted: "#6B675C",
        paper: "#EDE9DF",
        "paper-raised": "#F4F1EA",
        "paper-input": "#FBFAF6",
        line: "#DED9CC",
        "line-strong": "#C4BEAE",
        "fill-sunken": "#E6E1D4",
        rust: "#B4522A",
        "rust-light": "#D98A5F",
        "dark-muted": "#8A8578",
        "dark-body": "#B5AFA2",
        "dark-chip": "#C9C4B8",
        success: "#5C7A52",
        "success-bg": "#E8EFE3",
        "success-border": "#A8BE9B",
        "success-ink": "#3F5C34",
        "warn-bg": "#F7E4DC",
        "warn-border": "#DDA893",
        "warn-ink": "#8F3F1E",
        "streak-bg": "#F5E3D8",
        "streak-border": "#E0BCA5",
      },
      fontFamily: {
        serif: ["\"Instrument Serif\"", "Georgia", "serif"],
        sans: ["\"Space Grotesk\"", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["\"JetBrains Mono\"", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        xl2: "20px",
        card: "16px",
      },
      boxShadow: {
        card: "0 12px 28px rgba(20,19,15,0.07)",
        flashcard: "0 10px 26px rgba(20,19,15,0.06)",
        pill: "0 1px 3px rgba(20,19,15,0.1)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fade: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        blink: {
          "0%, 100%": { opacity: "0.3" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        rise: "rise 360ms ease both",
        fade: "fade 220ms ease both",
        blink: "blink 1.1s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
