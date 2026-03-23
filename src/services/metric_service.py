"""Metric service: orchestrates metric queries through the semantic registry and query executor.

This is the main service layer consumed by the API routes. It validates
requests against the semantic registry, delegates execution to the query
executor, and assembles structured responses.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from src.adapters.adapter_factory import create_adapter
from src.api.schemas import (
    DimensionDefinition,
    DimensionListResponse,
    ExplainMetricResponse,
    LineageInfo,
    MetricDefinition,
    MetricListResponse,
    NLQueryRequest,
    NLQueryResponse,
    QueryMetricRequest,
    QueryMetricResponse,
    QueryResultRow,
)
from src.core.config import get_settings
from src.core.enums import Grain
from src.llm.narration_service import NarrationService
from src.services.query_executor import QueryExecutor
from src.services.semantic_registry import SemanticRegistry


def _build_gemini_client(settings):
    """Create a GeminiClient if an API key is configured."""
    if not settings.gemini_api_key:
        return None
    from src.llm.gemini_client import GeminiClient
    return GeminiClient(api_key=settings.gemini_api_key, model_name=settings.gemini_model)


class MetricService:
    """Facade for governed metric operations."""

    def __init__(self) -> None:
        self._registry = SemanticRegistry()
        self._settings = get_settings()
        self._adapter = create_adapter(self._settings)
        self._executor = QueryExecutor(self._adapter)
        self._gemini = _build_gemini_client(self._settings)
        self._narration = NarrationService(
            enabled=self._settings.enable_narration,
            gemini_client=self._gemini,
        )

    def list_metrics(self) -> MetricListResponse:
        metrics = self._registry.list_metrics()
        return MetricListResponse(
            metrics=[
                MetricDefinition(
                    name=m.name,
                    description=m.description,
                    type="simple",
                    measure=m.measure,
                    aggregation=m.aggregation,
                    default_filters=m.default_filters,
                )
                for m in metrics
            ]
        )

    def list_dimensions(self) -> DimensionListResponse:
        dims = self._registry.list_dimensions()
        return DimensionListResponse(
            dimensions=[
                DimensionDefinition(
                    name=d.name, type=d.type, description=d.description
                )
                for d in dims
            ]
        )

    def query_metric(self, request: QueryMetricRequest) -> QueryMetricResponse:
        metric = self._registry.get_metric(request.metric)
        self._registry.validate_grain(request.grain)
        self._registry.validate_filters(request.metric, request.filters)

        raw_rows = self._executor.execute_metric(
            metric=metric,
            grain=request.grain,
            filters=request.filters,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        rows = [
            QueryResultRow(
                period=self._format_period(r["period"]),
                value=float(r["value"]),
            )
            for r in raw_rows
        ]

        start_str = request.start_date.isoformat() if request.start_date else "unbounded"
        end_str = request.end_date.isoformat() if request.end_date else "unbounded"

        lineage = LineageInfo(
            source="raw_app_data.margin_transactions",
            staging_model="stg_margin_calls",
            metric_name=metric.name,
            aggregation=metric.aggregation,
            filters_applied={**metric.default_filters, **request.filters},
            grain=request.grain.value,
            time_window={"start": start_str, "end": end_str},
        )

        narration = self._narration.narrate(
            metric_name=metric.name,
            rows=rows,
            filters={**metric.default_filters, **request.filters},
            grain=request.grain.value,
        )

        return QueryMetricResponse(
            metric=metric.name,
            grain=request.grain.value,
            filters={**metric.default_filters, **request.filters},
            time_window={"start": start_str, "end": end_str},
            rows=rows,
            lineage=lineage,
            narration=narration,
        )

    def explain_metric(self, metric_name: str) -> ExplainMetricResponse:
        metric = self._registry.get_metric(metric_name)
        return ExplainMetricResponse(
            metric=metric.name,
            description=metric.description,
            formula=f"{metric.aggregation}({metric.measure})",
            dimensions=[d.name for d in self._registry.list_dimensions()],
            default_filters=metric.default_filters,
            source_model="stg_margin_calls",
        )

    def nl_query(self, request: NLQueryRequest) -> NLQueryResponse:
        if self._gemini is None:
            return NLQueryResponse(
                question=request.question,
                translated={},
                error="Gemini API key not configured. Set GEMINI_API_KEY.",
            )

        from src.llm.nl_query_service import NLQueryService
        nl_service = NLQueryService(self._gemini)
        translated = nl_service.translate(request.question)

        if "error" in translated:
            return NLQueryResponse(
                question=request.question,
                translated=translated,
                error=translated.get("explanation", translated.get("raw_response", "Translation failed")),
            )

        if not request.execute:
            return NLQueryResponse(question=request.question, translated=translated)

        # Build and execute the translated query
        try:
            grain_val = Grain(translated.get("grain", "day"))
            start_date = (
                date.fromisoformat(translated["start_date"])
                if translated.get("start_date")
                else None
            )
            end_date = (
                date.fromisoformat(translated["end_date"])
                if translated.get("end_date")
                else None
            )
            query_req = QueryMetricRequest(
                metric=translated["metric"],
                grain=grain_val,
                filters=translated.get("filters", {}),
                start_date=start_date,
                end_date=end_date,
            )
            result = self.query_metric(query_req)
            return NLQueryResponse(
                question=request.question,
                translated=translated,
                result=result,
            )
        except (KeyError, ValueError) as exc:
            return NLQueryResponse(
                question=request.question,
                translated=translated,
                error=f"Execution failed: {exc}",
            )

    @staticmethod
    def _format_period(value: Any) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, date):
            return value.isoformat()
        return str(value)
