"""Unit tests for the narration service."""
from __future__ import annotations

from src.api.schemas import QueryResultRow
from src.llm.narration_service import NarrationService


class TestNarrationService:
    def test_disabled_returns_none(self) -> None:
        service = NarrationService(enabled=False)
        result = service.narrate(
            metric_name="net_margin_exposure",
            rows=[QueryResultRow(period="2025-01", value=100.0)],
            filters={"status_name": "CONFIRMED"},
            grain="month",
        )
        assert result is None

    def test_enabled_returns_string(self) -> None:
        service = NarrationService(enabled=True)
        result = service.narrate(
            metric_name="net_margin_exposure",
            rows=[QueryResultRow(period="2025-01", value=15500000.0)],
            filters={"status_name": "CONFIRMED"},
            grain="month",
        )
        assert result is not None
        assert "net_margin_exposure" in result
        assert "CONFIRMED" in result

    def test_empty_rows(self) -> None:
        service = NarrationService(enabled=True)
        result = service.narrate(
            metric_name="total_margin_calls",
            rows=[],
            filters={},
            grain="day",
        )
        assert result is not None
        assert "0 period(s)" in result
