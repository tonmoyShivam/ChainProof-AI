# VerityAI

Blockchain-based AI model provenance and integrity verification.

This repository (`ChainProof-AI`) hosts the **VerityAI** academic MVP: register AI model fingerprints on a local EVM, verify integrity via SHA-256 comparison against on-chain records, and inspect provenance history.

> **Milestone 8 (current):** Evaluation & finalization — measured gas/latency, Docker packaging, security hardening, comprehensive docs, Definition of Done.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.12, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Web3.py |
| Blockchain | Solidity 0.8.x, Hardhat (local chain id `31337`) |
| Database | PostgreSQL 16 (Docker Compose) |
| Storage | Local filesystem (`./storage`) |

## Repository layout

```
frontend/          React + Vite + Tailwind (+ Vitest helpers)
backend/           FastAPI application, Alembic, evaluation scripts
blockchain/        Hardhat workspace + gas measurement script
examples/ai-demo/  Safe JSON classifier demo (success + mismatch)
storage/           Off-chain model artifacts (gitignored contents)
docs/              Architecture, evaluation, security, DoD
docker-compose.yml PostgreSQL (+ optional API/FE profile)
.env.example       Environment placeholders only
```

## Prerequisites

- Node.js 20+ (22 recommended) and npm
- Python 3.12
- Docker Desktop (or Docker Engine + Compose) for PostgreSQL
- Git

## Quick start

### 1. Clone and configure environment

```bash
git clone <repository-url>
cd ChainProof-AI
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Edit `.env` only if your ports or credentials differ. Do not put real wallet keys in the repo.

### 2. Start PostgreSQL

```bash
docker compose up -d postgres
```

Then set in `.env`:

```bash
DATABASE_URL=postgresql+psycopg2://verityai:verityai@localhost:5432/verityai
```

If Docker is unavailable, keep the SQLite default. Automated tests always use ephemeral SQLite.

Verify: `docker compose ps` should show `verityai-postgres` healthy.

### 3. Local Hardhat node + contract deploy

```bash
cd blockchain
npm ci
npx hardhat node
```

In a second terminal:

```bash
cd blockchain
npx hardhat run scripts/deploy.js --network localhost
```

Copy the printed `ModelProvenance` address into `.env` as `BLOCKCHAIN_CONTRACT_ADDRESS`. Keep Hardhat account #0’s **public test** key in `BLOCKCHAIN_PRIVATE_KEY` for local signing only.

### 4. Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs (OpenAPI): http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  
- Health: http://localhost:8000/api/v1/health  
- Blockchain health: http://localhost:8000/api/v1/health/blockchain  

### 5. Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173.

### Optional: Compose API + frontend images

With Postgres + a host Hardhat node (and `BLOCKCHAIN_CONTRACT_ADDRESS` exported):

```bash
export BLOCKCHAIN_CONTRACT_ADDRESS=0xYourDeployedAddress
docker compose --profile full up -d --build
```

- API: http://localhost:8000  
- Frontend (nginx): http://localhost:8080  

Hardhat is **not** containerized by default (RPC ergonomics). Prefer host `npx hardhat node` for demos.

## Demo (success + mismatch)

See [`examples/ai-demo/README.md`](examples/ai-demo/README.md) and [`docs/ai-demo.md`](docs/ai-demo.md).

```bash
# Offline integrity path (no chain)
cd examples/ai-demo
python run_e2e_demo.py --skip-register

# Full path with running API + Hardhat
python run_e2e_demo.py
```

Expected: register → verify match → predict OK; one-byte tamper → verify mismatch → predict refused.

## Testing

```bash
# Backend
cd backend && source .venv/bin/activate && pytest -q

# Smart contracts
cd blockchain && npx hardhat test

# Frontend primary helpers
cd frontend && npm ci && npm test
```

## Evaluation (latency & gas)

**Never fabricate metrics.** Use the scripts and procedure in [`docs/evaluation.md`](docs/evaluation.md).

```bash
cd blockchain && npm run measure:gas
cd backend && python scripts/evaluate_latency.py --repeats 20 --size-kb 256 \
  --file ../examples/ai-demo/artifacts/demo_sentiment.json
```

A measured snapshot from the M8 environment: [`docs/evaluation-results.json`](docs/evaluation-results.json).

## Configuration

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL (Postgres or SQLite) |
| `JWT_SECRET` | HS256 secret (required strong when `APP_ENV=production`) |
| `BLOCKCHAIN_RPC_URL` | Hardhat RPC (default `http://127.0.0.1:8545`) |
| `BLOCKCHAIN_CONTRACT_ADDRESS` | Deployed `ModelProvenance` |
| `BLOCKCHAIN_PRIVATE_KEY` | Local signer (Hardhat #0 test key only) |
| `STORAGE_PATH` | Off-chain artifact directory |
| `CORS_ORIGINS` | Comma-separated browser origins |
| `RATE_LIMIT_AUTH_PER_MINUTE` | Auth endpoint limit (default 30) |
| `VITE_API_BASE_URL` | Frontend → API base |

## Documentation

| Doc | Content |
| --- | --- |
| [`docs/architecture.md`](docs/architecture.md) | Component diagram + OpenAPI pointers |
| [`docs/evaluation.md`](docs/evaluation.md) | How to measure latency/gas |
| [`docs/security.md`](docs/security.md) | Hardening + honest limitations |
| [`docs/definition-of-done.md`](docs/definition-of-done.md) | PRD §16 checklist |
| [`docs/ai-demo.md`](docs/ai-demo.md) | AI demo overview |

## Milestone roadmap

| Milestone | Focus |
| --- | --- |
| 1–7 | Foundation → hashing → contract → Web3 → DB/API → frontend → AI demo (merged) |
| **8** | Tests, measured evaluation, Docker, security notes, final docs (this PR) |

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Frontend health shows API error | Backend down / CORS | Start uvicorn; confirm `CORS_ORIGINS` includes `http://localhost:5173` |
| Blockchain health `unavailable` | Hardhat not started / wrong address | `npx hardhat node` then redeploy; update `BLOCKCHAIN_CONTRACT_ADDRESS` |
| Postgres connection refused | Compose not up | `docker compose up -d postgres` |
| `Refusing to start: JWT_SECRET` | Production env with weak secret | Set a strong `JWT_SECRET` or use `APP_ENV=development` locally |
| Auth `429 Too many requests` | Rate limit | Wait ~60s or raise `RATE_LIMIT_AUTH_PER_MINUTE` |
| Compose API cannot reach chain | Host RPC unreachable | Ensure Hardhat on host `:8545`; Linux needs `extra_hosts` (already set) |
| Port 5432 / 8000 / 8545 / 5173 in use | Local conflict | Stop the other process or change ports |

## Dependency pinning

- Backend: `backend/requirements.txt`
- Frontend: `frontend/package-lock.json`
- Blockchain: `blockchain/package-lock.json`

## License

Academic final-year project. See repository ownership for distribution terms.
