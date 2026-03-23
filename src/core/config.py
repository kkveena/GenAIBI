from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field

from src.core.enums import SourceMode


class AppSettings(BaseSettings):
    app_env: str = Field(default="dev")
    log_level: str = Field(default="INFO")

    source_mode: SourceMode = Field(default=SourceMode.JSON_DUCKDB)
    raw_json_glob: str = Field(default="./data/raw/*.json")

    sql_dsn: str = Field(default="")
    sql_source_schema: str = Field(default="risk_ops")
    sql_source_table: str = Field(default="vw_margin_transactions_consolidated")

    dbt_project_dir: str = Field(default="./dbt")
    dbt_profiles_dir: str = Field(default="./dbt")

    default_timezone: str = Field(default="UTC")
    llm_provider: str = Field(default="gemini")
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.0-flash")
    enable_narration: bool = Field(default=False)
    enable_tool_calling: bool = Field(default=False)
    enable_evals: bool = Field(default=False)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> AppSettings:
    return AppSettings()
