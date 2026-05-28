from __future__ import annotations

from typing import List, Tuple

from article_tracker.dedup.seen_store import SeenStore
from article_tracker.models.article import Article, SourceType
from article_tracker.utils.text import is_similar


class Deduplicator:
    def __init__(self, seen_store: SeenStore, title_threshold: float = 0.85, prefer_source: str = "top_journal"):
        self.seen = seen_store
        self.title_threshold = title_threshold
        self.prefer_source = prefer_source

    def deduplicate(self, articles: List[Article]) -> Tuple[List[Article], dict]:
        stats = {"input": len(articles), "dedup_doi": 0, "dedup_arxiv_id": 0, "dedup_title": 0, "new": 0}
        unique: List[Article] = []
        batch_keys: set[str] = set()

        for article in articles:
            dedup_key, key_type = self._find_dedup_key(article)
            if dedup_key and (self.seen.has(dedup_key) or dedup_key in batch_keys):
                if key_type == "doi":
                    stats["dedup_doi"] += 1
                elif key_type == "arxiv_id":
                    stats["dedup_arxiv_id"] += 1
                else:
                    stats["dedup_title"] += 1
                continue

            title_match = self._find_title_match(article, unique)
            if title_match is not None:
                self._merge_into(article, unique[title_match])
                stats["dedup_title"] += 1
                continue

            if dedup_key:
                batch_keys.add(dedup_key)
            unique.append(article)

        stats["new"] = len(unique)
        return unique, stats

    def mark_seen(self, articles: List[Article]) -> None:
        for article in articles:
            dedup_key, _ = self._find_dedup_key(article)
            if dedup_key and not self.seen.has(dedup_key):
                self.seen.mark(dedup_key, {"source": article.source_type.value, "title": article.title})

    def _find_dedup_key(self, article: Article) -> Tuple[str | None, str]:
        if article.dedup_key_doi:
            return f"doi:{article.dedup_key_doi}", "doi"
        if article.dedup_key_arxiv:
            return f"arxiv:{article.dedup_key_arxiv}", "arxiv_id"
        return None, ""

    def _find_title_match(self, article: Article, existing: List[Article]) -> int | None:
        for i, other in enumerate(existing):
            if is_similar(article.title, other.title, self.title_threshold):
                return i
        return None

    def _merge_into(self, src: Article, dst: Article) -> None:
        if self.prefer_source == "top_journal" and src.source_type == SourceType.top_journal:
            pass
        else:
            src, dst = dst, src
        if not dst.abstract and src.abstract:
            dst.abstract = src.abstract
        for url in src.code_links:
            if url not in dst.code_links:
                dst.code_links.append(url)
        if not dst.doi and src.doi:
            dst.doi = src.doi
        if not dst.arxiv_id and src.arxiv_id:
            dst.arxiv_id = src.arxiv_id
        if not dst.s2_id and src.s2_id:
            dst.s2_id = src.s2_id
