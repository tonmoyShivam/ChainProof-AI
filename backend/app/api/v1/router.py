"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import artifacts, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(artifacts.router, tags=["artifacts"])
