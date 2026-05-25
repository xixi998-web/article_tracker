from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List

from article_tracker.models.article import Article


class BaseSource(ABC):
    @abstractmethod
    def fetch(self, since: date | None = None) -> List[Article]:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError
