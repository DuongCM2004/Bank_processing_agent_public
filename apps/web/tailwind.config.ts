import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}", "./tests/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#11253b",
        mist: "#eef3f8",
        slate: "#5c7187",
        line: "#d5dfeb",
        accent: "#0f766e",
        accentSoft: "#dff4f1",
        warning: "#b45309",
        warningSoft: "#fff3db",
        danger: "#b42318",
        dangerSoft: "#fee4e2",
      },
      boxShadow: {
        panel: "0 20px 50px rgba(17, 37, 59, 0.08)",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
