# Frontend

React 18 + TypeScript + TailwindCSS + Vite SPA.

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server (port 5173) |
| `npm run build` | Production build |
| `npm run typecheck` | TypeScript check |
| `npm run lint` | ESLint |

## Setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

## Layout

- `src/api/` — HTTP client and typed endpoint modules
- `src/components/` — Shared UI (`layout/`)
- `src/providers/` — Auth (stub), TanStack Query
- `src/routes/` — Route tree
- `src/pages/` — Foundation pages (move to `features/` in Sprint 2+)
- `src/lib/` — Constants
- `src/styles/` — Design tokens

See [docs/PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md) §4.
