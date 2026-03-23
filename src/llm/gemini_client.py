"""Gemini client: thin wrapper around the Google Genai SDK.

Supports both narration (summarising deterministic results) and
natural-language-to-metric-query translation.
"""
from __future__ import annotations

from typing import Optional

import google.genai as genai


class GeminiClient:
    """Lightweight wrapper for the Gemini Generative AI API."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
            ),
        )
        return response.text
