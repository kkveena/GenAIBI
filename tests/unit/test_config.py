"""Unit tests for application configuration."""
from __future__ import annotations

import os

from src.core.config import AppSettings
from src.core.enums import SourceMode


class TestAppSettings:
    def test_defaults(self) -> None:
        settings = AppSettings(
            _env_file=None,
            source_mode=SourceMode.JSON_DUCKDB,
        )
        assert settings.app_env == "dev"
        assert settings.log_level == "INFO"
        assert settings.enable_narration is False
        assert settings.enable_tool_calling is False
        assert settings.enable_evals is False

    def test_source_mode_json(self) -> None:
        settings = AppSettings(
            _env_file=None,
            source_mode="json_duckdb",
        )
        assert settings.source_mode == SourceMode.JSON_DUCKDB

    def test_source_mode_sql(self) -> None:
        settings = AppSettings(
            _env_file=None,
            source_mode="sql_source",
        )
        assert settings.source_mode == SourceMode.SQL_SOURCE
