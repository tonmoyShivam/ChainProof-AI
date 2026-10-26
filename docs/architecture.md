# VerityAI Architecture

```
React (Vite)  →  FastAPI (/api/v1)  →  PostgreSQL
                      ↓
                 Web3.py → Hardhat local EVM (ModelProvenance)
                      ↓
                 Off-chain ./storage
```

## Components

| Layer | Path | Role |
| --- | --- | --- |
| Frontend | `frontend/` | Auth, dashboard, register/verify, details, history |
| Backend | `backend/` | FastAPI, JWT, hashing, registration/verification services |
| Blockchain | `blockchain/` | `ModelProvenance.sol`, Hardhat tests/deploy/gas script |
| Database | `docker-compose.yml` | PostgreSQL 16 (SQLite for tests / offline) |
| Storage | `storage/` | Off-chain artifacts |
| AI demo | `examples/ai-demo/` | Safe JSON classifier + register/verify before predict |

## API documentation

With the API running:

- OpenAPI / Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

Primary route groups under `/api/v1`: `health`, `auth`, `artifacts`, `models`, `dashboard`.

## Docker topology

Default Compose starts **Postgres only** (`docker compose up -d`).

Optional full profile (API + nginx frontend images):

```bash
docker compose --profile full up -d --build
```

Hardhat stays on the host (`npx hardhat node`) so RPC `8545` remains easy to reach; the API container uses `host.docker.internal:8545`.

## Related docs

- [`evaluation.md`](./evaluation.md) — latency/gas measurement procedure
- [`security.md`](./security.md) — hardening and limitations
- [`definition-of-done.md`](./definition-of-done.md) — PRD §16 checklist
- [`ai-demo.md`](./ai-demo.md) — Milestone 7 demo overview
