from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.core.enums import Grain


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    source_mode: str


class MetricDefinition(BaseModel):
    name: str
    description: str
    type: str
    measure: str
    aggregation: str
    default_filters: dict[str, Any] = Field(default_factory=dict)


class DimensionDefinition(BaseModel):
    name: str
    type: str
    description: str


class MetricListResponse(BaseModel):
    metrics: list[MetricDefinition]


class DimensionListResponse(BaseModel):
    dimensions: list[DimensionDefinition]


class QueryMetricRequest(BaseModel):
    metric: str
    grain: Grain = Grain.DAY
    filters: dict[str, Any] = Field(default_factory=dict)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class QueryResultRow(BaseModel):
    period: str
    value: float


class LineageInfo(BaseModel):
    source: str
    staging_model: str
    metric_name: str
    aggregation: str
    filters_applied: dict[str, Any]
    grain: str
    time_window: dict[str, str]


class QueryMetricResponse(BaseModel):
    metric: str
    grain: str
    filters: dict[str, Any]
    time_window: dict[str, str]
    rows: list[QueryResultRow]
    lineage: LineageInfo
    narration: Optional[str] = None


class ExplainMetricRequest(BaseModel):
    metric: str


class ExplainMetricResponse(BaseModel):
    metric: str
    description: str
    formula: str
    dimensions: list[str]
    default_filters: dict[str, Any]
    source_model: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
