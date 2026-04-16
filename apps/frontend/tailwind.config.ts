import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#102033",
        surface: "#f6f8fb",
        panel: "#ffffff",
        line: "#d8e1ea",
        muted: "#64748b",
        teal: "#0f766e",
        tealSoft: "#dff4f1",
        amber: "#b45309",
        amberSoft: "#fff3db",
        red: "#b42318",
        redSoft: "#fee4e2",
        blue: "#1d4ed8",
        blueSoft: "#dbeafe",
      },
      boxShadow: {
        panel: "0 14px 32px rgba(16, 32, 51, 0.08)",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
