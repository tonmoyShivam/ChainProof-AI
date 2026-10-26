# VerityAI Frontend

React + TypeScript + Vite + Tailwind dashboard for VerityAI.

## Milestone 6 status

Pages wired to real `/api/v1` endpoints:

- Landing, login, registration
- Dashboard (live stats + recent activity)
- Register model / verify model
- Model details + version history
- Settings (profile, logout, wallet placeholder)

Stack extras: TanStack Query, React Router, React Hook Form + Zod, Lucide icons, shadcn-style UI primitives.

## Commands

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

Ensure the FastAPI backend is running on port 8000 (Vite proxies `/api`). Copy `frontend/.env.example` to `.env` if you need a custom `VITE_API_BASE_URL`.

```bash
npm run build
```
