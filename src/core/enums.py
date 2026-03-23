from __future__ import annotations

from enum import StrEnum


class SourceMode(StrEnum):
    JSON_DUCKDB = "json_duckdb"
    SQL_SOURCE = "sql_source"


class StatusCode(StrEnum):
    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


STATUS_CODE_MAP: dict[int, StatusCode] = {
    4: StatusCode.CONFIRMED,
    5: StatusCode.PENDING,
    0: StatusCode.CANCELLED,
}


class Grain(StrEnum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"


class MetricType(StrEnum):
    SUM = "sum"
    COUNT_DISTINCT = "count_distinct"
    COUNT = "count"
