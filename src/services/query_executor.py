"""Query executor: builds and runs deterministic metric queries against the source adapter.

All business logic (field names, formulas, status mapping) is defined in dbt
and mirrored in the semantic registry. This module translates a governed metric
request into the corresponding SQL executed by the adapter.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from src.adapters.base_adapter import BaseSourceAdapter
from src.core.enums import Grain
from src.services.semantic_registry import MetricDef


_GRAIN_TRUNC: dict[Grain, str] = {
    Grain.DAY: "date_trunc('day', event_at)",
    Grain.MONTH: "date_trunc('month', event_at)",
    Grain.YEAR: "date_trunc('year', event_at)",
}


class QueryExecutor:
    """Builds and executes deterministic metric queries."""

    def __init__(self, adapter: BaseSourceAdapter) -> None:
        self._adapter = adapter

    def execute_metric(
        self,
        metric: MetricDef,
        grain: Grain,
        filters: dict[str, Any],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict[str, Any]]:
        agg_expr = self._build_aggregation(metric)
        trunc_expr = _GRAIN_TRUNC[grain]

        where_clauses = self._build_where(metric, filters, start_date, end_date)
        where_sql = f"where {' and '.join(where_clauses)}" if where_clauses else ""

        sql = (
            f"select {trunc_expr} as period, {agg_expr} as value "
            f"from stg_margin_calls "
            f"{where_sql} "
            f"group by period "
            f"order by period"
        )

        # The adapter operates on raw data; we need to run against staged data.
        # Build a CTE that applies staging logic, then run the metric query on top.
        full_sql = self._wrap_with_staging_cte(sql)
        return self._adapter.execute_query(full_sql)

    def _build_aggregation(self, metric: MetricDef) -> str:
        if metric.aggregation == "sum":
            return f"sum({metric.measure})"
        if metric.aggregation == "count_distinct":
            return f"count(distinct {metric.measure})"
        if metric.aggregation == "count":
            return f"count({metric.measure})"
        raise ValueError(f"Unsupported aggregation: {metric.aggregation}")

    def _build_where(
        self,
        metric: MetricDef,
        user_filters: dict[str, Any],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> list[str]:
        clauses: list[str] = []

        # Apply metric default filters.
        merged = {**metric.default_filters, **user_filters}
        for key, val in merged.items():
            clauses.append(f"{key} = '{val}'")

        # Apply threshold filters from metric definition.
        for key, val in metric.threshold_filters.items():
            if key.endswith("_gt"):
                col = key[:-3]
                clauses.append(f"{col} > {val}")

        # Date range.
        if start_date:
            clauses.append(f"event_at >= '{start_date.isoformat()}'")
        if end_date:
            clauses.append(f"event_at <= '{end_date.isoformat()}T23:59:59'")

        return clauses

    def _wrap_with_staging_cte(self, metric_sql: str) -> str:
        return (
            "with stg_margin_calls as (\n"
            "  select\n"
            "    cast(id as varchar) as call_id,\n"
            "    cast(acct_id as varchar) as account_id,\n"
            "    cast(mc_amt as decimal(18,2)) as margin_amount_usd,\n"
            "    cast(collateral_val as decimal(18,2)) as collateral_amount_usd,\n"
            "    cast(mc_amt as decimal(18,2))\n"
            "      - cast(collateral_val as decimal(18,2)) as net_val,\n"
            "    case\n"
            "      when st_cd = 4 then 'CONFIRMED'\n"
            "      when st_cd = 5 then 'PENDING'\n"
            "      when st_cd = 0 then 'CANCELLED'\n"
            "      else 'UNKNOWN'\n"
            "    end as status_name,\n"
            "    cast(event_ts as timestamp) as event_at\n"
            "  from margin_transactions\n"
            ")\n" + metric_sql
        )
