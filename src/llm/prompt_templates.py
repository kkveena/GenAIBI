"""Prompt templates for LLM narration.

All prompts are versioned and explicit. The LLM receives only grounded
context: metric name, filters, grain, and the deterministic result rows.
"""
from __future__ import annotations

from typing import Any

NARRATION_TEMPLATE_V1 = """You are a BI narration assistant. Your job is to summarize
the deterministic result of a governed metric query. Do NOT invent numbers,
formulas, or field names. Only restate the data provided below.

Metric: {metric_name}
Grain: {grain}
Filters applied: {filters}

Result rows:
{rows_text}

Provide a concise, professional summary of the above result. Restate the
metric name and filters used. Do not speculate beyond the data shown."""


def build_narration_prompt(
    metric_name: str,
    rows: list[Any],
    filters: dict[str, Any],
    grain: str,
) -> str:
    rows_text = "\n".join(
        f"  {r.period}: {r.value:,.2f}" for r in rows
    ) if rows else "  (no data)"

    filter_text = ", ".join(f"{k}={v}" for k, v in filters.items()) if filters else "none"

    return NARRATION_TEMPLATE_V1.format(
        metric_name=metric_name,
        grain=grain,
        filters=filter_text,
        rows_text=rows_text,
    )
