"""Integration tests for the FastAPI application."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert data["source_mode"] == "json_duckdb"


class TestMetricsEndpoint:
    def test_list_metrics(self, client: TestClient) -> None:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["metrics"]) == 3
        names = {m["name"] for m in data["metrics"]}
        assert names == {"net_margin_exposure", "high_risk_breaches", "total_margin_calls"}

    def test_metric_has_required_fields(self, client: TestClient) -> None:
        resp = client.get("/metrics")
        metric = resp.json()["metrics"][0]
        assert "name" in metric
        assert "description" in metric
        assert "measure" in metric
        assert "aggregation" in metric


class TestDimensionsEndpoint:
    def test_list_dimensions(self, client: TestClient) -> None:
        resp = client.get("/dimensions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["dimensions"]) == 3
        names = {d["name"] for d in data["dimensions"]}
        assert names == {"event_at", "status_name", "account_id"}


class TestQueryMetricEndpoint:
    def test_query_net_margin_exposure(self, client: TestClient) -> None:
        resp = client.post("/query-metric", json={
            "metric": "net_margin_exposure",
            "grain": "month",
            "filters": {},
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "net_margin_exposure"
        assert data["grain"] == "month"
        assert len(data["rows"]) == 1
        assert data["rows"][0]["value"] == pytest.approx(15_500_000.00)
        assert data["lineage"]["metric_name"] == "net_margin_exposure"

    def test_query_total_margin_calls(self, client: TestClient) -> None:
        resp = client.post("/query-metric", json={
            "metric": "total_margin_calls",
            "grain": "month",
            "filters": {},
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["rows"][0]["value"] == 10

    def test_query_high_risk_breaches(self, client: TestClient) -> None:
        resp = client.post("/query-metric", json={
            "metric": "high_risk_breaches",
            "grain": "month",
            "filters": {},
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["rows"][0]["value"] == 5

    def test_query_unknown_metric_returns_404(self, client: TestClient) -> None:
        resp = client.post("/query-metric", json={
            "metric": "nonexistent",
            "grain": "day",
        })
        assert resp.status_code == 404

    def test_query_invalid_filter_returns_400(self, client: TestClient) -> None:
        resp = client.post("/query-metric", json={
            "metric": "total_margin_calls",
            "grain": "day",
            "filters": {"bogus_field": "x"},
        })
        assert resp.status_code == 400

    def test_query_with_narration_disabled(self, client: TestClient) -> None:
        resp = client.post("/query-metric", json={
            "metric": "total_margin_calls",
            "grain": "month",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["narration"] is None


class TestExplainMetricEndpoint:
    def test_explain_net_margin_exposure(self, client: TestClient) -> None:
        resp = client.post("/explain-metric", json={
            "metric": "net_margin_exposure",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "net_margin_exposure"
        assert "sum" in data["formula"]
        assert "net_val" in data["formula"]
        assert data["source_model"] == "stg_margin_calls"

    def test_explain_unknown_metric(self, client: TestClient) -> None:
        resp = client.post("/explain-metric", json={
            "metric": "nonexistent",
        })
        assert resp.status_code == 404
