"""Contract tests: verify that staged data matches the expected data contract.

These tests ensure the semantic bridge produces the correct field names,
types, and computed values — the same contract that dbt enforces.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.adapters.duckdb_adapter import DuckDBAdapter


class TestStagingContract:
    def test_all_canonical_fields_present(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        expected = {
            "call_id", "account_id", "margin_amount_usd",
            "collateral_amount_usd", "net_val", "status_name", "event_at",
        }
        for row in rows:
            assert set(row.keys()) == expected

    def test_call_id_not_null(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        for row in rows:
            assert row["call_id"] is not None
            assert row["call_id"] != ""

    def test_account_id_not_null(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        for row in rows:
            assert row["account_id"] is not None

    def test_status_name_accepted_values(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        valid = {"CONFIRMED", "PENDING", "CANCELLED", "UNKNOWN"}
        for row in rows:
            assert row["status_name"] in valid

    def test_net_val_equals_margin_minus_collateral(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        for row in rows:
            expected = float(row["margin_amount_usd"]) - float(row["collateral_amount_usd"])
            assert float(row["net_val"]) == pytest.approx(expected)

    def test_event_at_not_null(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        for row in rows:
            assert row["event_at"] is not None

    def test_margin_amount_not_null(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        for row in rows:
            assert row["margin_amount_usd"] is not None

    def test_call_id_unique(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        ids = [r["call_id"] for r in rows]
        assert len(ids) == len(set(ids))
