# VerityAI Backend

Python 3.12 FastAPI service for AI model provenance and integrity verification.

## Milestone status

- FastAPI app with CORS and `/api/v1` routing
- Health: `GET /api/v1/health`, `GET /api/v1/health/blockchain`
- **Milestone 2:** chunked SHA-256, upload validation, safe local storage
  - `POST /api/v1/artifacts/hash` — validate + hash (no storage)
  - `POST /api/v1/artifacts/upload` — validate + hash + store under `storage/artifacts/`
- **Milestone 4:** Web3.py ↔ `ModelProvenance` register/verify
- **Milestone 5:** SQLAlchemy users/models/versions/verification_logs, Alembic, JWT auth, dashboard APIs
  - Auth: `POST /auth/register|login|logout`, `GET /auth/me`
  - Models: register/list/get/versions/history/verify/verification-history
  - Dashboard: `GET /dashboard/stats`, `GET /dashboard/recent-activity` (real aggregates)
- Settings via environment variables (see root `.env.example`)

## Local setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
# Prefer repo-root .env; STORAGE_PATH should point at ../storage from backend/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

OpenAPI docs: http://localhost:8000/docs

### Smoke upload

```bash
curl -s -F "file=@./sample.pt;type=application/octet-stream" \
  http://localhost:8000/api/v1/artifacts/hash
```

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```
