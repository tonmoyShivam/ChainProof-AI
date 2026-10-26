# Evaluation procedure (latency & gas)

VerityAI records **measured** results only. Do not invent targets or paste unverified numbers into reports.

## Gas (smart contract)

Requires Node dependencies in `blockchain/`:

```bash
cd blockchain
npm ci
npm run measure:gas
# equivalent: npx hardhat run scripts/measure_gas.js
```

This deploys a fresh `ModelProvenance` on the in-process Hardhat network and prints JSON with:

- `gas.registerModel` — receipt `gasUsed` for root registration
- `gas.registerVersion` — receipt `gasUsed` for a child version
- `gas.verifyModelEstimate` — `estimateGas` for the view `verifyModel` call

Save the console JSON (or redirect) into your lab notes. A snapshot from this environment is in [`evaluation-results.json`](./evaluation-results.json).

## Hashing / API latency

From `backend/` with the venv active:

```bash
cd backend
source .venv/bin/activate
python scripts/evaluate_latency.py --repeats 20 --size-kb 256 \
  --file ../examples/ai-demo/artifacts/demo_sentiment.json
```

Optional live API timings (Hardhat + uvicorn must already be running with a deployed contract):

```bash
python scripts/evaluate_latency.py --repeats 5 \
  --file ../examples/ai-demo/artifacts/demo_sentiment.json \
  --api-base http://127.0.0.1:8000
```

If the API or chain is down, the `api` section reports `skipped` with a reason — that is expected, not a fabricated zero.

## What to report

| Metric | Source |
| --- | --- |
| Registration gas | `measure_gas.js` → `gas.registerModel` |
| Version gas | `measure_gas.js` → `gas.registerVersion` |
| Verify gas (estimate) | `measure_gas.js` → `gas.verifyModelEstimate` |
| Hash latency (memory/file) | `evaluate_latency.py` |
| Register / verify wall time | `evaluate_latency.py --api-base` when stack is up |

Re-run after material contract or hashing changes; treat prior JSON as historical, not a guarantee.
