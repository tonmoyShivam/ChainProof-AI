# VerityAI

Blockchain-based AI model provenance and integrity verification.

This repository (`ChainProof-AI`) hosts the **VerityAI** academic MVP: register AI model fingerprints on a local EVM, verify integrity via SHA-256 comparison against on-chain records, and inspect provenance history.

> **Milestone 1 (current):** project foundation — layout, React/FastAPI/Hardhat/PostgreSQL scaffolding, env templates, and health endpoints. Hashing, contracts, auth UI, and registration come in later milestones.

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
frontend/          React + Vite + Tailwind
backend/           FastAPI application
blockchain/        Hardhat workspace
storage/           Off-chain model artifacts (gitignored contents)
docs/              Project documentation
docker-compose.yml PostgreSQL service
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

Verify: `docker compose ps` should show `verityai-postgres` healthy.

### 3. Backend

```bash
cd backend
python3.12 -m venv .venv
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Blockchain health: http://localhost:8000/api/v1/health/blockchain

### 4. Local Hardhat node (optional for M1 blockchain health = ok)

```bash
cd blockchain
npm install
npx hardhat node
```

With the node running, `GET /api/v1/health/blockchain` should report `"status": "ok"` and `"connected": true`. Without it, the endpoint correctly returns `"unavailable"` (never treated as a successful verification).

### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the home page shows VerityAI branding and live infrastructure status.

## Verify foundation

With the backend running (and optionally Hardhat + Postgres):

```bash
# Application health
curl -s http://localhost:8000/api/v1/health

# Blockchain RPC probe
curl -s http://localhost:8000/api/v1/health/blockchain

# Backend smoke tests
cd backend && source .venv/bin/activate && pytest -q
```

Expected `/api/v1/health` payload shape:

```json
{ "status": "ok", "service": "VerityAI", "environment": "development" }
```

## Dependency pinning

- Backend: `backend/requirements.txt` (exact versions)
- Frontend: `frontend/package-lock.json`
- Blockchain: `blockchain/package-lock.json`

Commit lockfiles; reinstall with `npm ci` / `pip install -r requirements.txt` for reproducible setups.

## Milestone roadmap

| Milestone | Focus |
| --- | --- |
| **1** | Foundation (this PR) |
| 2 | SHA-256 hashing, upload validation, local storage |
| 3 | `ModelProvenance.sol`, Hardhat tests, local deploy |
| 4 | Web3.py registration / verification integration |
| 5 | PostgreSQL models, Alembic, auth, full API |
| 6 | Dashboard, register/verify UI, history pages |
| 7 | Lightweight AI demo model |
| 8 | Tests, evaluation, Docker packaging, report |

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Frontend health shows API error | Backend not running / CORS | Start uvicorn; confirm `CORS_ORIGINS` includes `http://localhost:5173` |
| Blockchain health `unavailable` | Hardhat node not started | `cd blockchain && npx hardhat node` |
| Postgres connection refused | Compose not up | `docker compose up -d postgres` |
| Port 5432 / 8000 / 8545 in use | Local conflict | Stop the other process or change ports in `.env` / compose |

## License

Academic final-year project. See repository ownership for distribution terms.
