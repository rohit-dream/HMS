import type { Config } from "tailwindcss";
import { tokens } from "./src/styles/tokens";

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      colors: {
        primary: tokens.colors.primary,
        secondary: tokens.colors.secondary,
        accent: tokens.colors.accent,
        sidebar: tokens.colors.sidebar,
        "sidebar-active": tokens.colors.sidebarActive,
        "sidebar-text": tokens.colors.sidebarText,
        surface: tokens.colors.surface,
        "surface-secondary": tokens.colors.surfaceSecondary,
        card: tokens.colors.card,
        hover: tokens.colors.hover,
        foreground: tokens.colors.foreground,
        muted: tokens.colors.textMuted,
        border: tokens.colors.border,
        "border-light": tokens.colors.borderLight,
        success: tokens.colors.success,
        error: tokens.colors.error,
        warning: tokens.colors.warning,
      },
      width: {
        sidebar: tokens.layout.sidebarWidth,
        "sidebar-collapsed": tokens.layout.sidebarCollapsedWidth,
      },
      boxShadow: {
        card: "0 1px 3px rgba(0, 0, 0, 0.08)",
        "card-md": "0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.06)",
      },
      backgroundImage: {
        "app-gradient": tokens.colors.surface,
        "primary-gradient": tokens.colors.primary,
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-out",
        "scale-in": "scale-in 0.25s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
