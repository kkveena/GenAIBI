from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    DimensionListResponse,
    ErrorResponse,
    ExplainMetricRequest,
    ExplainMetricResponse,
    MetricListResponse,
    QueryMetricRequest,
    QueryMetricResponse,
)
from src.services.metric_service import MetricService

router = APIRouter()


def _get_service() -> MetricService:
    return MetricService()


@router.get(
    "/metrics",
    response_model=MetricListResponse,
    responses={500: {"model": ErrorResponse}},
)
def list_metrics() -> MetricListResponse:
    service = _get_service()
    return service.list_metrics()


@router.get(
    "/dimensions",
    response_model=DimensionListResponse,
    responses={500: {"model": ErrorResponse}},
)
def list_dimensions() -> DimensionListResponse:
    service = _get_service()
    return service.list_dimensions()


@router.post(
    "/query-metric",
    response_model=QueryMetricResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def query_metric(request: QueryMetricRequest) -> QueryMetricResponse:
    service = _get_service()
    try:
        return service.query_metric(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/explain-metric",
    response_model=ExplainMetricResponse,
    responses={404: {"model": ErrorResponse}},
)
def explain_metric(request: ExplainMetricRequest) -> ExplainMetricResponse:
    service = _get_service()
    try:
        return service.explain_metric(request.metric)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
