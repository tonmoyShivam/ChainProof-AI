# VerityAI Architecture (Milestone 1)

High-level layout for the local MVP foundation:

```
React (Vite)  →  FastAPI (/api/v1)  →  PostgreSQL
                      ↓
                 Web3.py → Hardhat local EVM
                      ↓
                 Off-chain ./storage
```

## Components

| Layer | Path | Role in M1 |
| --- | --- | --- |
| Frontend | `frontend/` | Vite + React + Tailwind scaffold; home page health probes |
| Backend | `backend/` | FastAPI app; `/api/v1/health` and `/api/v1/health/blockchain` |
| Blockchain | `blockchain/` | Hardhat 2.22 + Solidity 0.8.24 config (contracts in M3) |
| Database | `docker-compose.yml` | PostgreSQL 16 |
| Storage | `storage/` | Placeholder for off-chain model artifacts (M2) |

Full workflows (registration, verification, versioning) are specified in the project PRD and implemented in later milestones.
