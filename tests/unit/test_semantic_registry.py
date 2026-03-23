"""Unit tests for the semantic registry."""
from __future__ import annotations

import pytest

from src.core.enums import Grain
from src.services.semantic_registry import SemanticRegistry


class TestSemanticRegistryMetrics:
    def test_list_metrics_returns_three(self, registry: SemanticRegistry) -> None:
        metrics = registry.list_metrics()
        assert len(metrics) == 3

    def test_get_net_margin_exposure(self, registry: SemanticRegistry) -> None:
        m = registry.get_metric("net_margin_exposure")
        assert m.measure == "net_val"
        assert m.aggregation == "sum"
        assert m.default_filters == {"status_name": "CONFIRMED"}

    def test_get_high_risk_breaches(self, registry: SemanticRegistry) -> None:
        m = registry.get_metric("high_risk_breaches")
        assert m.aggregation == "count_distinct"
        assert m.threshold_filters == {"margin_amount_usd_gt": 5_000_000}

    def test_get_total_margin_calls(self, registry: SemanticRegistry) -> None:
        m = registry.get_metric("total_margin_calls")
        assert m.aggregation == "count_distinct"
        assert m.default_filters == {}

    def test_unknown_metric_raises(self, registry: SemanticRegistry) -> None:
        with pytest.raises(KeyError, match="Unknown metric"):
            registry.get_metric("nonexistent_metric")


class TestSemanticRegistryDimensions:
    def test_list_dimensions_returns_three(self, registry: SemanticRegistry) -> None:
        dims = registry.list_dimensions()
        assert len(dims) == 3

    def test_get_event_at(self, registry: SemanticRegistry) -> None:
        d = registry.get_dimension("event_at")
        assert d.type == "time"

    def test_get_status_name(self, registry: SemanticRegistry) -> None:
        d = registry.get_dimension("status_name")
        assert d.type == "categorical"

    def test_unknown_dimension_raises(self, registry: SemanticRegistry) -> None:
        with pytest.raises(KeyError, match="Unknown dimension"):
            registry.get_dimension("nonexistent_dim")


class TestSemanticRegistryValidation:
    def test_validate_grain_day(self, registry: SemanticRegistry) -> None:
        registry.validate_grain(Grain.DAY)

    def test_validate_grain_month(self, registry: SemanticRegistry) -> None:
        registry.validate_grain(Grain.MONTH)

    def test_validate_filters_valid(self, registry: SemanticRegistry) -> None:
        registry.validate_filters("net_margin_exposure", {"status_name": "CONFIRMED"})

    def test_validate_filters_unknown_dimension(self, registry: SemanticRegistry) -> None:
        with pytest.raises(ValueError, match="Unknown filter dimension"):
            registry.validate_filters("net_margin_exposure", {"bogus_field": "x"})
