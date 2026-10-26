"""VerityAI FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.security_hardening import SimpleRateLimitMiddleware, enforce_settings_security
from app.db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    enforce_settings_security(settings)
    application = FastAPI(
        title=settings.app_name,
        description=(
            "Blockchain-based AI model provenance and integrity verification API. "
            "Interactive OpenAPI: /docs (Swagger) and /redoc."
        ),
        version="0.8.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if settings.app_env.lower() not in {"test", "testing"}:
        application.add_middleware(
            SimpleRateLimitMiddleware,
            limit=settings.rate_limit_auth_per_minute,
            window=60.0,
        )

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
