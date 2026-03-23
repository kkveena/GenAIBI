from __future__ import annotations

from fastapi import FastAPI

from src.api.routes_health import router as health_router
from src.api.routes_metrics import router as metrics_router
from src.core.config import get_settings
from src.core.logging import setup_logging


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="Semantic GenAI for BI",
        version="0.1.0",
        description="Deterministic, audit-ready natural-language BI over margin and risk data.",
    )

    app.include_router(health_router, tags=["health"])
    app.include_router(metrics_router, tags=["metrics"])

    return app


app = create_app()
