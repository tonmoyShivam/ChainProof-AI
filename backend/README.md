# VerityAI Backend

Python 3.12 FastAPI service for AI model provenance and integrity verification.

## Milestone 1 status

- FastAPI app with CORS and `/api/v1` routing
- Health endpoints: `GET /api/v1/health`, `GET /api/v1/health/blockchain`
- Settings via environment variables (see root `.env.example`)
- Package layout for models, services, repositories, blockchain, and storage

## Local setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

OpenAPI docs: http://localhost:8000/docs

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```
