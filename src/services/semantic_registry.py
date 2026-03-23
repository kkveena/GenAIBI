"""Semantic registry: in-memory representation of governed metrics and dimensions.

Reads metric/dimension definitions from the dbt semantic YAML and exposes
them for the API and metric service to consume. Business logic lives in dbt;
this module only mirrors the contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.core.enums import Grain


@dataclass(frozen=True)
class MetricDef:
    name: str
    description: str
    measure: str
    aggregation: str
    default_filters: dict[str, Any] = field(default_factory=dict)
    threshold_filters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DimensionDef:
    name: str
    type: str
    description: str


# ---------------------------------------------------------------------------
# Hard-coded registry mirroring dbt/models/marts/margin_risk.yml
# In a production build this would be parsed from YAML at startup.
# ---------------------------------------------------------------------------

_METRICS: dict[str, MetricDef] = {
    "net_margin_exposure": MetricDef(
        name="net_margin_exposure",
        description="Total net margin exposure: sum of net_val for confirmed margin calls.",
        measure="net_val",
        aggregation="sum",
        default_filters={"status_name": "CONFIRMED"},
    ),
    "high_risk_breaches": MetricDef(
        name="high_risk_breaches",
        description="Count of confirmed margin calls exceeding $5M threshold.",
        measure="call_id",
        aggregation="count_distinct",
        default_filters={"status_name": "CONFIRMED"},
        threshold_filters={"margin_amount_usd_gt": 5_000_000},
    ),
    "total_margin_calls": MetricDef(
        name="total_margin_calls",
        description="Total count of all margin calls regardless of status.",
        measure="call_id",
        aggregation="count_distinct",
    ),
}

_DIMENSIONS: dict[str, DimensionDef] = {
    "event_at": DimensionDef(
        name="event_at",
        type="time",
        description="Event date/time for time-based analysis.",
    ),
    "status_name": DimensionDef(
        name="status_name",
        type="categorical",
        description="Margin call status (CONFIRMED, PENDING, CANCELLED, UNKNOWN).",
    ),
    "account_id": DimensionDef(
        name="account_id",
        type="categorical",
        description="Account identifier for account-level analysis.",
    ),
}

_VALID_GRAINS: set[Grain] = {Grain.DAY, Grain.MONTH, Grain.YEAR}


class SemanticRegistry:
    """Read-only registry of governed metrics and dimensions."""

    def get_metric(self, name: str) -> MetricDef:
        if name not in _METRICS:
            raise KeyError(f"Unknown metric: '{name}'. Available: {list(_METRICS.keys())}")
        return _METRICS[name]

    def list_metrics(self) -> list[MetricDef]:
        return list(_METRICS.values())

    def get_dimension(self, name: str) -> DimensionDef:
        if name not in _DIMENSIONS:
            raise KeyError(f"Unknown dimension: '{name}'. Available: {list(_DIMENSIONS.keys())}")
        return _DIMENSIONS[name]

    def list_dimensions(self) -> list[DimensionDef]:
        return list(_DIMENSIONS.values())

    def validate_grain(self, grain: Grain) -> None:
        if grain not in _VALID_GRAINS:
            raise ValueError(f"Unsupported grain: '{grain}'. Supported: {sorted(_VALID_GRAINS)}")

    def validate_filters(self, metric_name: str, filters: dict[str, Any]) -> None:
        for key in filters:
            if key not in _DIMENSIONS:
                raise ValueError(
                    f"Unknown filter dimension: '{key}'. "
                    f"Available: {list(_DIMENSIONS.keys())}"
                )
