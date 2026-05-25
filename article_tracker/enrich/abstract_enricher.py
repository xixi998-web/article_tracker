from __future__ import annotations

import logging
from typing import List

from article_tracker.config.config_schema import OpenAlexConfig, S2Config
from article_tracker.infra import http_client
from article_tracker.models.article import AbstractSource, Article

logger = logging.getLogger(__name__)

S2_FIELDS = "paperId,abstract"
OPENALEX_FIELDS = "id,abstract"


class AbstractEnricher:
    def __init__(self, s2_config: S2Config, openalex_config: OpenAlexConfig):
        self.s2_config = s2_config
        self.openalex_config = openalex_config

    def enrich(self, articles: List[Article]) -> dict:
        stats = {"s2": 0, "openalex": 0, "crossref": 0, "none": 0, "skipped": 0}
        for article in articles:
            if article.abstract:
                stats["skipped"] += 1
                continue
            abstract, source = self._fallback(article)
            if abstract:
                article.abstract = abstract
                article.abstract_source = source
                stats[source.value] += 1
            else:
                article.abstract_source = AbstractSource.none_
                stats["none"] += 1
        return stats

    def _fallback(self, article: Article) -> tuple[str | None, AbstractSource]:
        result = self._try_s2(article)
        if result:
            return result, AbstractSource.semantic_scholar
        result = self._try_openalex(article)
        if result:
            return result, AbstractSource.openalex
        result = self._try_crossref(article)
        if result:
            return result, AbstractSource.crossref
        return None, AbstractSource.none_

    def _try_s2(self, article: Article) -> str | None:
        if not self.s2_config.api_key and not article.s2_id and not article.doi:
            return None
        headers = {}
        if self.s2_config.api_key:
            headers["x-api-key"] = self.s2_config.api_key
        try:
            if article.s2_id:
                resp = http_client.get(
                    f"{self.s2_config.base_url}/paper/{article.s2_id}",
                    params={"fields": S2_FIELDS}, headers=headers,
                )
            elif article.doi:
                resp = http_client.get(
                    f"{self.s2_config.base_url}/paper/DOI:{article.doi}",
                    params={"fields": S2_FIELDS}, headers=headers,
                )
            else:
                return None
            resp.raise_for_status()
            return resp.json().get("abstract") or None
        except Exception:
            return None

    def _try_openalex(self, article: Article) -> str | None:
        if not article.doi and not self.openalex_config.email:
            return None
        try:
            if article.doi:
                params = {"filter": f"doi:{article.doi}"}
            else:
                return None
            if self.openalex_config.email:
                params["mailto"] = self.openalex_config.email
            resp = http_client.get(f"{self.openalex_config.base_url}/works", params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if results:
                inverted = results[0].get("abstract_inverted_index")
                if inverted:
                    return self._inverted_index_to_text(inverted)
            return None
        except Exception:
            return None

    def _try_crossref(self, article: Article) -> str | None:
        if not article.doi:
            return None
        try:
            resp = http_client.get(
                f"https://api.crossref.org/works/{article.doi}",
                headers={"User-Agent": "article-tracker/0.1 (mailto:contact@example.com)"},
            )
            resp.raise_for_status()
            return resp.json().get("message", {}).get("abstract") or None
        except Exception:
            return None

    @staticmethod
    def _inverted_index_to_text(inverted: dict) -> str:
        if not inverted:
            return ""
        positions: list[tuple[int, str]] = []
        for word, indices in inverted.items():
            for idx in indices:
                positions.append((idx, word))
        positions.sort()
        return " ".join(w for _, w in positions)
