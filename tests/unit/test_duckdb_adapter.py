"""Unit tests for the DuckDB source adapter."""
from __future__ import annotations

import pytest

from src.adapters.duckdb_adapter import DuckDBAdapter


class TestDuckDBAdapter:
    def test_get_staged_data_row_count(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        assert len(rows) == 10

    def test_staged_data_has_canonical_fields(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        expected_fields = {
            "call_id", "account_id", "margin_amount_usd",
            "collateral_amount_usd", "net_val", "status_name", "event_at",
        }
        assert set(rows[0].keys()) == expected_fields

    def test_status_mapping_confirmed(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        mc001 = next(r for r in rows if r["call_id"] == "MC-001")
        assert mc001["status_name"] == "CONFIRMED"

    def test_status_mapping_pending(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        mc004 = next(r for r in rows if r["call_id"] == "MC-004")
        assert mc004["status_name"] == "PENDING"

    def test_status_mapping_cancelled(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        mc006 = next(r for r in rows if r["call_id"] == "MC-006")
        assert mc006["status_name"] == "CANCELLED"

    def test_net_val_computation(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        mc001 = next(r for r in rows if r["call_id"] == "MC-001")
        expected = 7500000.00 - 5000000.00
        assert float(mc001["net_val"]) == pytest.approx(expected)

    def test_net_val_negative(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.get_staged_data()
        mc004 = next(r for r in rows if r["call_id"] == "MC-004")
        expected = 1500000.00 - 1600000.00
        assert float(mc004["net_val"]) == pytest.approx(expected)

    def test_execute_query_raw(self, duckdb_adapter: DuckDBAdapter) -> None:
        rows = duckdb_adapter.execute_query("select count(*) as cnt from margin_transactions")
        assert rows[0]["cnt"] == 10

    def test_missing_json_raises(self, tmp_path: any) -> None:
        with pytest.raises(FileNotFoundError):
            DuckDBAdapter(json_glob=str(tmp_path / "nonexistent" / "*.json"))
