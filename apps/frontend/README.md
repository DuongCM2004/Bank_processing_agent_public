# Web

Operations dashboard scaffold for banking document review.

Stack:

- React 18
- TypeScript
- Vite
- TailwindCSS
- React Router
- TanStack Query
- Vitest + React Testing Library

Project structure:

```text
apps/frontend/
├─ public/
├─ src/
│  ├─ api/
│  ├─ app/
│  ├─ components/
│  │  ├─ layout/
│  │  └─ ui/
│  ├─ features/
│  │  ├─ audit/
│  │  ├─ cases/
│  │  ├─ documents/
│  │  └─ review/
│  ├─ pages/
│  │  ├─ audit/
│  │  ├─ cases/
│  │  ├─ dashboard/
│  │  ├─ not-found/
│  │  ├─ review/
│  │  └─ settings/
│  ├─ styles/
│  └─ lib/
├─ tests/
└─ package.json
```

Design rules:

- optimize for dashboard-style operations work
- keep route handlers and API transport concerns separate from presentational components
- make workflow status, findings, and audit context easy to scan

Environment configuration:

- Local frontend defaults live in `.env.example`.
- Frontend variables use the `VITE_OPS_AGENT_` prefix.
- `VITE_OPS_AGENT_API_BASE_URL` points the dashboard at the backend API.
- Do not put secrets in `VITE_*` variables; Vite exposes them to the browser bundle.
- Environment-level templates live in `../../infra/environments/`.
