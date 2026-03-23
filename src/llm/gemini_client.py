"""Gemini client: thin wrapper around the Google Generative AI SDK.

Supports both narration (summarising deterministic results) and
natural-language-to-metric-query translation.
"""
from __future__ import annotations

from typing import Optional

import google.generativeai as genai


class GeminiClient:
    """Lightweight wrapper for the Gemini Generative AI API."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash",
    ) -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        response = self._model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
            ),
        )
        return response.text
