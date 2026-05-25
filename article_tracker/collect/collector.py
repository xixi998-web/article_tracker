from __future__ import annotations

from datetime import date
from typing import List

from article_tracker.config.config_schema import (
    UnifiedConfig,
)
from article_tracker.models.article import Article
from article_tracker.source.arxiv_source import ArxivSource
from article_tracker.source.base import BaseSource
from article_tracker.source.top_journal_source import TopJournalSource


class Collector:
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self._sources: List[BaseSource] = []
        self._init_sources()

    def _init_sources(self) -> None:
        source_filter = self.config.source_filter
        if source_filter in ("all", "arxiv") and self.config.arxiv.enabled:
            self._sources.append(ArxivSource(self.config.arxiv, self.config.freshness))
        if source_filter in ("all", "top_journal") and self.config.top_journal.enabled:
            self._sources.append(
                TopJournalSource(self.config.top_journal, self.config.s2, self.config.openalex)
            )

    def collect(self, source: str = "all", since: date | None = None) -> dict[str, List[Article]]:
        results: dict[str, List[Article]] = {}
        for src in self._sources:
            if source != "all" and src.name != source:
                continue
            try:
                articles = src.fetch(since=since)
                results[src.name] = articles
            except Exception as e:
                results[src.name] = []
                import logging
                logging.getLogger(__name__).warning(f"Source {src.name} failed: {e}")
        return results
