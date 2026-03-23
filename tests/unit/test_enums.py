"""Unit tests for core enums and status code mapping."""
from __future__ import annotations

from src.core.enums import (
    Grain,
    MetricType,
    SourceMode,
    StatusCode,
    STATUS_CODE_MAP,
)


class TestSourceMode:
    def test_json_duckdb_value(self) -> None:
        assert SourceMode.JSON_DUCKDB == "json_duckdb"

    def test_sql_source_value(self) -> None:
        assert SourceMode.SQL_SOURCE == "sql_source"


class TestStatusCodeMap:
    def test_confirmed_mapping(self) -> None:
        assert STATUS_CODE_MAP[4] == StatusCode.CONFIRMED

    def test_pending_mapping(self) -> None:
        assert STATUS_CODE_MAP[5] == StatusCode.PENDING

    def test_cancelled_mapping(self) -> None:
        assert STATUS_CODE_MAP[0] == StatusCode.CANCELLED

    def test_unknown_not_in_map(self) -> None:
        assert 99 not in STATUS_CODE_MAP


class TestGrain:
    def test_day(self) -> None:
        assert Grain.DAY == "day"

    def test_month(self) -> None:
        assert Grain.MONTH == "month"

    def test_year(self) -> None:
        assert Grain.YEAR == "year"
