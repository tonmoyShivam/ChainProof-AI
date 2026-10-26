"""Startup security checks and lightweight request safeguards."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import Settings

logger = logging.getLogger("verityai.security")

DEFAULT_JWT_SECRETS = {
    "change-me-verityai-dev-secret",
    "test-secret",
    "live-test-secret",
    "fail-secret",
}


def enforce_settings_security(settings: Settings) -> None:
    """Refuse insecure production configuration; warn in development."""
    weak_jwt = settings.jwt_secret.strip() in DEFAULT_JWT_SECRETS or len(settings.jwt_secret) < 16
    if settings.app_env.lower() in {"production", "prod"}:
        if weak_jwt:
            raise RuntimeError(
                "Refusing to start: set a strong JWT_SECRET when APP_ENV=production"
            )
        if not settings.blockchain_private_key:
            logger.warning("BLOCKCHAIN_PRIVATE_KEY is empty in production")
    elif weak_jwt:
        logger.warning(
            "JWT_SECRET is a development default — change it before any shared deployment"
        )


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory per-IP rate limit for auth endpoints (best-effort for local MVP).

    Not a substitute for a production gateway / WAF.
    """

    def __init__(self, app, *, limit: int = 30, window: float = 60.0):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/auth/register"):
            client = request.client.host if request.client else "unknown"
            now = time.monotonic()
            bucket = self._hits[client]
            while bucket and now - bucket[0] > self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many auth attempts; try again later"},
                )
            bucket.append(now)
        return await call_next(request)
