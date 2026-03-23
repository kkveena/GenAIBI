from __future__ import annotations

from typing import Any

from src.adapters.base_adapter import BaseSourceAdapter


class SQLSourceAdapter(BaseSourceAdapter):
    """Adapter for direct SQL source (curated view/table).

    Phase 1 stub: uses DuckDB in-memory with a registered table
    to simulate a SQL source. Replace with a real DB connection
    when deploying against an actual warehouse.
    """

    def __init__(self, dsn: str, schema: str, table: str) -> None:
        self._dsn = dsn
        self._schema = schema
        self._table = table

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "SQLSourceAdapter requires a configured database connection. "
            "Use json_duckdb mode for local development."
        )

    def get_staged_data(self) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "SQLSourceAdapter requires a configured database connection. "
            "Use json_duckdb mode for local development."
        )

    def close(self) -> None:
        pass
