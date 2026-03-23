"""Natural-language query service: translates user questions into governed metric queries.

Uses Gemini to map a free-text question to the closest governed metric,
grain, filters, and date range — then executes the query through the
deterministic pipeline so numbers are always trustworthy.
"""
from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Optional

from src.llm.gemini_client import GeminiClient
from src.services.semantic_registry import SemanticRegistry


_NL_TO_QUERY_TEMPLATE = """You are a BI query translator.  Your job is to convert a
natural-language question into a structured metric query against a governed
semantic layer.

## Available metrics
{metrics_catalog}

## Available filter dimensions
{dimensions_catalog}

## Available grains
day, month, year

## Instructions
Given the user question below, return ONLY a JSON object with these fields:
- "metric": one of the metric names above (string)
- "grain": one of day / month / year (string)
- "filters": dict of dimension→value (may be empty {{}})
- "start_date": ISO date string or null
- "end_date": ISO date string or null
- "explanation": one-sentence explanation of how you mapped the question

Do NOT invent metric names.  If the question cannot be mapped, return:
{{"error": "unmappable", "explanation": "..."}}

## User question
{question}
"""


class NLQueryService:
    """Translate natural-language questions into semantic-layer queries."""

    def __init__(self, gemini_client: GeminiClient) -> None:
        self._client = gemini_client
        self._registry = SemanticRegistry()

    def translate(self, question: str) -> dict[str, Any]:
        metrics = self._registry.list_metrics()
        dims = self._registry.list_dimensions()

        metrics_catalog = "\n".join(
            f"- {m.name}: {m.description}  (aggregation={m.aggregation}, measure={m.measure}, default_filters={m.default_filters})"
            for m in metrics
        )
        dimensions_catalog = "\n".join(
            f"- {d.name} ({d.type}): {d.description}" for d in dims
        )

        prompt = _NL_TO_QUERY_TEMPLATE.format(
            metrics_catalog=metrics_catalog,
            dimensions_catalog=dimensions_catalog,
            question=question,
        )

        raw = self._client.generate(prompt, temperature=0.0)

        # Extract JSON from the response (may be wrapped in markdown fences)
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if not json_match:
            return {"error": "parse_error", "raw_response": raw}

        try:
            parsed = json.loads(json_match.group())
        except json.JSONDecodeError:
            return {"error": "parse_error", "raw_response": raw}

        return parsed
