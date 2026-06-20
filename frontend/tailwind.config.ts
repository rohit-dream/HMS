import type { Config } from "tailwindcss";
import { tokens } from "./src/styles/tokens";

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: tokens.colors.primary,
        sidebar: tokens.colors.sidebar,
        surface: tokens.colors.surface,
        muted: tokens.colors.textMuted,
        border: tokens.colors.border,
        success: tokens.colors.success,
        error: tokens.colors.error,
        warning: tokens.colors.warning,
      },
      width: {
        sidebar: tokens.layout.sidebarWidth,
      },
    },
  },
  plugins: [],
};

export default config;
