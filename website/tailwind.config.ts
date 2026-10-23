import type { Config } from "tailwindcss";

// Colours are CSS variables (see app/globals.css) so light and dark mode
// switch in one place and Tailwind opacity modifiers still work.
const v = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: v("paper"),
        "paper-2": v("paper-2"),
        card: v("card"),
        tape: v("tape"),
        ink: v("ink"),
        "ink-2": v("ink-2"),
        "ink-3": v("ink-3"),
        line: v("line"),
        "line-2": v("line-2"),
        green: v("green"),
        "green-ink": v("green-ink"),
        marker: v("marker"),
        "marker-ink": v("marker-ink"),
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "Consolas", "monospace"],
      },
      boxShadow: {
        soft: "0 1px 0 rgb(0 0 0 / .04), 0 12px 32px -12px rgb(0 0 0 / .18)",
        lift: "0 1px 0 rgb(0 0 0 / .04), 0 28px 64px -28px rgb(0 0 0 / .4)",
      },
      keyframes: {
        marquee: { to: { transform: "translateX(-50%)" } },
        blink: { "50%": { opacity: "0" } },
        pulse2: { "50%": { opacity: ".3" } },
      },
      animation: {
        marquee: "marquee 40s linear infinite",
        blink: "blink 1s steps(1) infinite",
        pulse2: "pulse2 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
