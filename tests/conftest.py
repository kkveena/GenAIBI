"""Shared pytest fixtures for the Semantic GenAI BI test suite."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Generator

import pytest

from src.adapters.duckdb_adapter import DuckDBAdapter
from src.services.semantic_registry import SemanticRegistry


SAMPLE_DATA: list[dict[str, Any]] = [
    {"id": "MC-001", "acct_id": "ACCT-100", "mc_amt": 7500000.00, "collateral_val": 5000000.00, "st_cd": 4, "event_ts": "2025-01-05T10:30:00Z"},
    {"id": "MC-002", "acct_id": "ACCT-101", "mc_amt": 3200000.00, "collateral_val": 2800000.00, "st_cd": 4, "event_ts": "2025-01-07T14:15:00Z"},
    {"id": "MC-003", "acct_id": "ACCT-102", "mc_amt": 12000000.00, "collateral_val": 8000000.00, "st_cd": 4, "event_ts": "2025-01-10T09:00:00Z"},
    {"id": "MC-004", "acct_id": "ACCT-100", "mc_amt": 1500000.00, "collateral_val": 1600000.00, "st_cd": 5, "event_ts": "2025-01-12T11:00:00Z"},
    {"id": "MC-005", "acct_id": "ACCT-103", "mc_amt": 6000000.00, "collateral_val": 4500000.00, "st_cd": 4, "event_ts": "2025-01-15T16:45:00Z"},
    {"id": "MC-006", "acct_id": "ACCT-104", "mc_amt": 900000.00, "collateral_val": 950000.00, "st_cd": 0, "event_ts": "2025-01-18T08:30:00Z"},
    {"id": "MC-007", "acct_id": "ACCT-105", "mc_amt": 8200000.00, "collateral_val": 6100000.00, "st_cd": 4, "event_ts": "2025-01-20T13:20:00Z"},
    {"id": "MC-008", "acct_id": "ACCT-101", "mc_amt": 4500000.00, "collateral_val": 4000000.00, "st_cd": 5, "event_ts": "2025-01-22T10:00:00Z"},
    {"id": "MC-009", "acct_id": "ACCT-106", "mc_amt": 15000000.00, "collateral_val": 10000000.00, "st_cd": 4, "event_ts": "2025-01-25T15:30:00Z"},
    {"id": "MC-010", "acct_id": "ACCT-102", "mc_amt": 2000000.00, "collateral_val": 2100000.00, "st_cd": 0, "event_ts": "2025-01-28T09:45:00Z"},
]


@pytest.fixture
def sample_json_path(tmp_path: Path) -> Path:
    """Write sample data to a temp JSON file and return the glob path."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    fp = raw_dir / "margin_transactions.json"
    fp.write_text(json.dumps(SAMPLE_DATA))
    return raw_dir / "*.json"


@pytest.fixture
def duckdb_adapter(sample_json_path: Path) -> Generator[DuckDBAdapter, None, None]:
    adapter = DuckDBAdapter(json_glob=str(sample_json_path))
    yield adapter
    adapter.close()


@pytest.fixture
def registry() -> SemanticRegistry:
    return SemanticRegistry()


@pytest.fixture(autouse=True)
def set_env_for_tests(sample_json_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set environment variables for test runs."""
    monkeypatch.setenv("SOURCE_MODE", "json_duckdb")
    monkeypatch.setenv("RAW_JSON_GLOB", str(sample_json_path))
    monkeypatch.setenv("ENABLE_NARRATION", "false")
