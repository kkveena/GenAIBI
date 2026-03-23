from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseSourceAdapter(ABC):
    """Interface for source data adapters."""

    @abstractmethod
    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """Execute a SQL query and return rows as list of dicts."""

    @abstractmethod
    def get_staged_data(self) -> list[dict[str, Any]]:
        """Return all staged margin call data with canonical field names."""

    @abstractmethod
    def close(self) -> None:
        """Release resources."""
