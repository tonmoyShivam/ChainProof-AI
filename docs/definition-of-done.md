# Definition of Done checklist (PRD §16)

Status as of Milestone 8 finalization. Items marked **remaining** are documented limitations, not silent passes.

| Criterion | Status | Evidence |
| --- | --- | --- |
| Application starts via documented instructions | Done | Root `README.md` Quick start |
| Frontend talks to real backend | Done | Vite `VITE_API_BASE_URL` / proxy; dashboard uses live `/api/v1` |
| Backend connects to local deployed contract | Done | Web3.py + `BLOCKCHAIN_*` env; `/health/blockchain` |
| Registration creates confirmed chain record | Done | `POST /models/register` + Hardhat receipt |
| Fingerprint retrievable from contract | Done | `getModel` / model detail API |
| Original artifact verifies successfully | Done | Verify API + AI demo E2E |
| Modified artifact fails verification | Done | Tamper path in `examples/ai-demo` |
| Version history preserves prior records | Done | Contract + `/models/{id}/history` |
| Unauthorized operations rejected | Done | JWT on protected routes; auth tests |
| Migrations work on clean DB | Done | Alembic `migrations/`; Compose Postgres |
| Automated tests pass | Done | `pytest`, `hardhat test`, `vitest` (primary UI helpers) |
| API errors handled safely | Done | Structured statuses; unavailable ≠ verified |
| No credentials committed | Done | `.env` gitignored; example placeholders only |
| README: setup, testing, troubleshooting | Done | Root README (M8 rewrite) |
| No fabricated verification / dashboard stats | Done | Live queries; evaluation scripts measure only |
| Docker where feasible | Done | Compose Postgres; optional `--profile full` API+FE images |
| Evaluation procedure for latency/gas | Done | `docs/evaluation.md` + measured snapshot JSON |
| Formal security audit | Remaining | See `docs/security.md` — MVP hardening only |
| Full browser E2E suite (Playwright/Cypress) | Remaining | Manual demo + unit helpers; not a browser automation suite |
| Public-network / testnet deployment | Remaining | Local Hardhat only by design for this MVP |

## Final acceptance (PRD §18)

A reviewer can: start the stack locally → register a model → inspect provenance → verify original → modify a copy → observe mismatch → inspect version history. Demonstration path: `examples/ai-demo/README.md`.
