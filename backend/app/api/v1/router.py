"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import artifacts, auth, dashboard, health, models

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(artifacts.router, tags=["artifacts"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(dashboard.router)
