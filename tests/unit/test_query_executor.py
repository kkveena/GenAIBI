"""Unit tests for the query executor."""
from __future__ import annotations

from datetime import date

import pytest

from src.adapters.duckdb_adapter import DuckDBAdapter
from src.core.enums import Grain
from src.services.query_executor import QueryExecutor
from src.services.semantic_registry import SemanticRegistry


class TestQueryExecutorNetMarginExposure:
    def test_net_margin_exposure_monthly(
        self, duckdb_adapter: DuckDBAdapter, registry: SemanticRegistry
    ) -> None:
        executor = QueryExecutor(duckdb_adapter)
        metric = registry.get_metric("net_margin_exposure")
        rows = executor.execute_metric(
            metric=metric,
            grain=Grain.MONTH,
            filters={},
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        assert len(rows) == 1
        # Confirmed calls: MC-001 (2.5M), MC-002 (0.4M), MC-003 (4M),
        # MC-005 (1.5M), MC-007 (2.1M), MC-009 (5M) = 15.5M
        total = float(rows[0]["value"])
        assert total == pytest.approx(15_500_000.00)

    def test_net_margin_exposure_daily(
        self, duckdb_adapter: DuckDBAdapter, registry: SemanticRegistry
    ) -> None:
        executor = QueryExecutor(duckdb_adapter)
        metric = registry.get_metric("net_margin_exposure")
        rows = executor.execute_metric(
            metric=metric,
            grain=Grain.DAY,
            filters={},
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        # 6 confirmed calls on distinct days
        assert len(rows) == 6


class TestQueryExecutorHighRiskBreaches:
    def test_high_risk_breaches_monthly(
        self, duckdb_adapter: DuckDBAdapter, registry: SemanticRegistry
    ) -> None:
        executor = QueryExecutor(duckdb_adapter)
        metric = registry.get_metric("high_risk_breaches")
        rows = executor.execute_metric(
            metric=metric,
            grain=Grain.MONTH,
            filters={},
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        assert len(rows) == 1
        # Confirmed calls with mc_amt > 5M: MC-001 (7.5M), MC-003 (12M),
        # MC-005 (6M), MC-007 (8.2M), MC-009 (15M) = 5 breaches
        assert int(rows[0]["value"]) == 5


class TestQueryExecutorTotalMarginCalls:
    def test_total_margin_calls_monthly(
        self, duckdb_adapter: DuckDBAdapter, registry: SemanticRegistry
    ) -> None:
        executor = QueryExecutor(duckdb_adapter)
        metric = registry.get_metric("total_margin_calls")
        rows = executor.execute_metric(
            metric=metric,
            grain=Grain.MONTH,
            filters={},
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        assert len(rows) == 1
        assert int(rows[0]["value"]) == 10


class TestQueryExecutorFilters:
    def test_filter_by_status(
        self, duckdb_adapter: DuckDBAdapter, registry: SemanticRegistry
    ) -> None:
        executor = QueryExecutor(duckdb_adapter)
        metric = registry.get_metric("total_margin_calls")
        rows = executor.execute_metric(
            metric=metric,
            grain=Grain.MONTH,
            filters={"status_name": "PENDING"},
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        assert len(rows) == 1
        assert int(rows[0]["value"]) == 2

    def test_date_range_filter(
        self, duckdb_adapter: DuckDBAdapter, registry: SemanticRegistry
    ) -> None:
        executor = QueryExecutor(duckdb_adapter)
        metric = registry.get_metric("total_margin_calls")
        rows = executor.execute_metric(
            metric=metric,
            grain=Grain.MONTH,
            filters={},
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 15),
        )
        assert len(rows) == 1
        # MC-001..MC-005 = 5 calls in first half of Jan
        assert int(rows[0]["value"]) == 5
