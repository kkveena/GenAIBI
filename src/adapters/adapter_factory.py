from __future__ import annotations

from src.adapters.base_adapter import BaseSourceAdapter
from src.adapters.duckdb_adapter import DuckDBAdapter
from src.adapters.sql_adapter import SQLSourceAdapter
from src.core.config import AppSettings
from src.core.enums import SourceMode


def create_adapter(settings: AppSettings) -> BaseSourceAdapter:
    """Factory: return the correct source adapter for the configured mode."""
    if settings.source_mode == SourceMode.JSON_DUCKDB:
        return DuckDBAdapter(json_glob=settings.raw_json_glob)

    if settings.source_mode == SourceMode.SQL_SOURCE:
        return SQLSourceAdapter(
            dsn=settings.sql_dsn,
            schema=settings.sql_source_schema,
            table=settings.sql_source_table,
        )

    raise ValueError(f"Unknown source mode: {settings.source_mode}")
