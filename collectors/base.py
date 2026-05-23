"""Base collector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from core.models import Item


class BaseCollector(ABC):
    name: str

    @abstractmethod
    def collect(self, since: datetime | None = None) -> list[Item]:
        """Fetch new content since the given timestamp. None = fetch recent batch."""
        ...

    @abstractmethod
    def validate_config(self) -> bool:
        """Check required config is present."""
        ...
