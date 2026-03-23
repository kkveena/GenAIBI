"""Narration service: optional LLM-based narration of deterministic query results.

Behind a feature flag (ENABLE_NARRATION). When disabled, returns None.
When enabled, generates a human-readable summary of the metric result
using only grounded data — never inventing formulas or numbers.
"""
from __future__ import annotations

from typing import Any, Optional

from src.llm.prompt_templates import build_narration_prompt


class NarrationService:
    """Generate narrated summaries of metric results."""

    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    def narrate(
        self,
        metric_name: str,
        rows: list[Any],
        filters: dict[str, Any],
        grain: str,
    ) -> Optional[str]:
        if not self._enabled:
            return None

        prompt = build_narration_prompt(
            metric_name=metric_name,
            rows=rows,
            filters=filters,
            grain=grain,
        )

        # Phase 1 stub: return the prompt as a template narration.
        # In production, this would call the configured LLM provider.
        return self._stub_narrate(metric_name, rows, filters, grain)

    @staticmethod
    def _stub_narrate(
        metric_name: str,
        rows: list[Any],
        filters: dict[str, Any],
        grain: str,
    ) -> str:
        total = sum(r.value for r in rows) if rows else 0
        filter_desc = ", ".join(f"{k}={v}" for k, v in filters.items()) if filters else "none"
        return (
            f"The governed metric '{metric_name}' returned {len(rows)} "
            f"period(s) at {grain} grain with filters [{filter_desc}]. "
            f"Aggregate total: {total:,.2f}."
        )
