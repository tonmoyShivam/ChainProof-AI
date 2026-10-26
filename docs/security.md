# Security notes (MVP)

Academic MVP hardening — **not** a security audit.

## Mitigations present

| Area | Behavior |
| --- | --- |
| Secrets | `.env` / Compose env only; `.env.example` has placeholders and a public Hardhat test key |
| JWT | Weak/default `JWT_SECRET` is **refused** when `APP_ENV=production` / `prod` |
| Auth brute force | In-memory rate limit on `/api/v1/auth/login` and `/register` (disabled when `APP_ENV=test`) |
| Uploads | Extension allow-list + configurable size cap; streaming SHA-256 |
| Demo model | JSON weights — avoids pickle/joblib deserialization |
| Blockchain failures | RPC/contract errors → `VERIFICATION_UNAVAILABLE`, never `VERIFIED` |
| Authz | Protected model routes require Bearer JWT |

## Remaining limitations (honest)

- Rate limiting is process-local (not Redis / gateway); unsuitable as sole production control.
- JWT is HS256 shared secret — no refresh-token rotation or revocation list beyond logout client-side.
- Local Hardhat keys and default JWT are for **dev only**.
- No formal threat model, penetration test, or smart-contract audit.
- File storage is local filesystem without malware scanning.
- CORS is configurable but often wide open in local `.env`.
- Docker API image still starts with the documented development JWT unless you override it.

## Quick hardening checklist for a shared demo

1. Set a long random `JWT_SECRET`.
2. Set `APP_ENV=production` only after (1).
3. Do not reuse Hardhat private keys on any public network.
4. Put the API behind TLS and a reverse proxy with real rate limits.
