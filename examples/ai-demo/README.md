# VerityAI AI Demonstration (Milestone 7)

Lightweight end-to-end demo of **provenance + integrity**, not model quality.

## What this is

- Tiny bag-of-words logistic sentiment classifier
- Stored as **safe JSON** (`verityai-demo-linear-v1`) — no pickle/joblib loading
- Register SHA-256 via the real VerityAI API / local Hardhat contract
- **Predict only after verification succeeds**
- Tampered copy must fail verification and must not be loaded

A matching hash proves the file bytes match the registered artifact. It does **not** prove accuracy, safety, ethics, or the real-world identity of a creator.

## Files

| Path | Purpose |
| --- | --- |
| `demo_classifier.py` | Train/load/predict helpers (JSON only) |
| `train_demo_model.py` | Write `artifacts/demo_sentiment.json` |
| `infer_after_verify.py` | Verify then predict (offline hash or API) |
| `run_e2e_demo.py` | Full success + mismatch demonstration |
| `artifacts/demo_sentiment.json` | Checked-in demo weights (no secrets) |

## Offline demo (no blockchain)

```bash
cd examples/ai-demo
python3 train_demo_model.py
HASH=$(python3 -c 'from pathlib import Path; from train_demo_model import sha256_file; print(sha256_file(Path("artifacts/demo_sentiment.json")))')
python3 infer_after_verify.py --model artifacts/demo_sentiment.json --offline-hash "$HASH"
python3 run_e2e_demo.py --skip-register
```

Expected: original verifies and predicts; tampered copy exits non-zero with `INTEGRITY_MISMATCH`.

## Full stack demo (API + Hardhat)

Prerequisites:

1. Hardhat node: `cd blockchain && npx hardhat node`
2. Deploy: `npx hardhat run scripts/deploy.js --network localhost`
3. Set `BLOCKCHAIN_CONTRACT_ADDRESS` and Hardhat test `BLOCKCHAIN_PRIVATE_KEY` in root `.env`
4. Backend: `cd backend && source .venv/bin/activate && alembic upgrade head && uvicorn app.main:app --port 8000`

Then:

```bash
cd examples/ai-demo
python3 run_e2e_demo.py --api-base http://127.0.0.1:8000
```

## Safety notes

- Loader rejects any file that is not `format: verityai-demo-linear-v1`
- Do not replace this with pickle deserialization of untrusted uploads
- Demo corpus is synthetic toy data for academic demonstration only
