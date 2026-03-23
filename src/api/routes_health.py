from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import HealthResponse
from src.core.config import get_settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(source_mode=settings.source_mode.value)
