# VerityAI

Blockchain-based AI model provenance and integrity verification.

This repository (`ChainProof-AI`) hosts the **VerityAI** academic MVP: register AI model fingerprints on a local EVM, verify integrity via SHA-256 comparison against on-chain records, and inspect provenance history.

> **Milestone 5 (current):** PostgreSQL/SQLAlchemy schema, Alembic migrations, JWT auth, and complete `/api/v1` registration/verification/dashboard APIs. React dashboard UI is Milestone 6.

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

### 2. Start PostgreSQL (recommended)

```bash
docker compose up -d postgres
```

Then set in `.env`:

```bash
DATABASE_URL=postgresql+psycopg2://verityai:verityai@localhost:5432/verityai
```

If Docker is unavailable (e.g. some cloud agent VMs), keep the SQLite default `DATABASE_URL=sqlite+pysqlite:///./verityai.db`. Schema and Alembic migrations are the same; automated tests use SQLite for portability.

Verify Postgres: `docker compose ps` should show `verityai-postgres` healthy.

### 3. Backend

```bash
cd backend
python3.12 -m venv .venv
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Blockchain health: http://localhost:8000/api/v1/health/blockchain

### 4. Local Hardhat node + contract deploy

```bash
cd blockchain
npm install
npx hardhat node
```

In a second terminal:

```bash
cd blockchain
npx hardhat run scripts/deploy.js --network localhost
# or: npm run deploy:localhost
```

Copy the printed `ModelProvenance` address into `.env` as `BLOCKCHAIN_CONTRACT_ADDRESS`. Keep the Hardhat account #0 test key in `BLOCKCHAIN_PRIVATE_KEY` for local signing only.

With the node running, `GET /api/v1/health/blockchain` should report `"status": "ok"` and `"connected": true`. Without it, the endpoint correctly returns `"unavailable"` (never treated as a successful verification).

Auth + register / verify (after backend is up):

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"dev@example.com","password":"password123","display_name":"Dev"}'
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"dev@example.com","password":"password123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

printf 'weights-v1' > /tmp/model.pt
curl -s -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/model.pt" -F "name=Demo" -F "version=1.0.0" \
  http://localhost:8000/api/v1/models/register
# use returned model_id:
curl -s -F "file=@/tmp/model.pt" -F "model_id=<model_id>" \
  http://localhost:8000/api/v1/models/verify
```

### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the home page shows VerityAI branding and live infrastructure status.

## Verify foundation + hashing

With the backend running (and optionally Hardhat + Postgres):

```bash
# Application health
curl -s http://localhost:8000/api/v1/health

# Blockchain RPC probe
curl -s http://localhost:8000/api/v1/health/blockchain

# Hash an allowed artifact (example)
printf 'demo-weights' > /tmp/demo.pt
curl -s -F "file=@/tmp/demo.pt;type=application/octet-stream" \
  http://localhost:8000/api/v1/artifacts/hash

# Backend tests (health + hashing + storage)
cd backend && source .venv/bin/activate && pytest -q

# Smart contract tests
cd ../blockchain && npx hardhat test
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
| 1 | Foundation (merged) |
| 2 | SHA-256 hashing, upload validation, local storage (merged) |
| 3 | `ModelProvenance.sol`, Hardhat tests, local deploy (merged) |
| 4 | Web3.py registration / verification integration (merged) |
| **5** | PostgreSQL models, Alembic, auth, full API (this PR) |
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
