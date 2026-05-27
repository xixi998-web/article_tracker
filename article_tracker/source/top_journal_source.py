from __future__ import annotations

import re
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from article_tracker.config.config_schema import OpenAlexConfig, S2Config, TopJournalSourceConfig
from article_tracker.infra import http_client
from article_tracker.models.article import Article, SourceType
from article_tracker.source.base import BaseSource


def build_watchlist(md_path: str, pool: str = "all") -> List[Dict[str, Any]]:
    p = Path(md_path)
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8")
    entries = []
    current_family = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            current_family = line[3:].strip()
        elif line.startswith("- ") and current_family:
            rest = line[2:].strip()
            name = rest
            issn = None
            m = re.search(r"\((ISSN[:\s]*[\d-]+)\)", rest, re.IGNORECASE)
            if m:
                issn = m.group(1).replace("ISSN", "").strip(": ").strip()
                name = re.sub(r"\s*\(ISSN[:\s]*[\d-]+\)", "", rest, flags=re.IGNORECASE).strip()
            entries.append({"family": current_family, "name": name, "issn": issn})
    if pool != "all":
        entries = [e for e in entries if pool.lower() in e.get("family", "").lower()]
    return entries


class TopJournalSource(BaseSource):
    def __init__(
        self,
        config: TopJournalSourceConfig,
        s2_config: S2Config,
        openalex_config: OpenAlexConfig,
        core_keywords: List[str] | None = None,
    ):
        self.config = config
        self.s2_config = s2_config
        self.openalex_config = openalex_config
        self.core_keywords = core_keywords or []

    @property
    def name(self) -> str:
        return "top_journal"

    def fetch(self, since: date | None = None) -> List[Article]:
        since = since or (date.today() - timedelta(days=self.config.since_days))
        watchlist = self._get_watchlist()
        if not watchlist:
            return []

        all_articles: List[Article] = []
        seen_ids: set[str] = set()

        if self.core_keywords:
            top_keywords = self.core_keywords[:3]
            for entry in watchlist:
                for kw in top_keywords:
                    articles = self._fetch_from_s2(entry, since, extra_query=kw)
                    for a in articles:
                        aid = a.doi or a.arxiv_id or a.s2_id or a.title
                        if aid not in seen_ids:
                            seen_ids.add(aid)
                            all_articles.append(a)
                    time.sleep(1.0)
        else:
            for entry in watchlist[:self.config.max_per_journal]:
                articles = self._fetch_from_s2(entry, since)
                all_articles.extend(articles)
                time.sleep(1.0)

        self._enrich_openalex_metadata(all_articles)
        return all_articles

    def _get_watchlist(self) -> List[Dict[str, Any]]:
        if self.config.watchlist:
            return [e.model_dump() for e in self.config.watchlist]
        if self.config.watchlist_path:
            return build_watchlist(self.config.watchlist_path)
        return []

    def _fetch_from_s2(self, watchlist_entry: Dict[str, Any], since: date, extra_query: str = "") -> List[Article]:
        api_key = self.s2_config.api_key
        base_url = self.s2_config.base_url
        journal_name = watchlist_entry.get("name", "")
        if not journal_name:
            return []

        headers = {}
        if api_key:
            headers["x-api-key"] = api_key

        query = f"{journal_name} {extra_query}".strip()

        since_str = since.isoformat()
        params = {
            "query": query,
            "fields": "paperId,title,authors,abstract,publicationDate,externalIds,url,openAccessPdf,journal",
            "limit": str(self.config.max_per_journal),
            "publicationDateOrYear": since_str,
        }

        try:
            resp = http_client.get(f"{base_url}/paper/search", params=params, headers=headers)
            if resp.status_code == 429:
                import logging
                logging.getLogger(__name__).warning("S2 429 rate limit, sleeping 30s...")
                time.sleep(30)
                resp = http_client.get(f"{base_url}/paper/search", params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        articles = []
        for paper in data.get("data", []):
            article = self._parse_s2_paper(paper, journal_name)
            if article:
                articles.append(article)
        return articles

    def _parse_s2_paper(self, paper: Dict[str, Any], journal_name: str) -> Optional[Article]:
        title = paper.get("title") or ""
        if not title.strip():
            return None

        authors = [a.get("name", "") for a in paper.get("authors", []) if a.get("name")]
        abstract = paper.get("abstract") or ""
        pub_date = paper.get("publicationDate")
        s2_id = paper.get("paperId")
        ext_ids = paper.get("externalIds") or {}
        doi = ext_ids.get("DOI")
        arxiv_id = ext_ids.get("ArXiv")
        url = paper.get("url")
        oa_pdf = paper.get("openAccessPdf") or {}
        pdf_url = oa_pdf.get("url") if isinstance(oa_pdf, dict) else None

        journal_info = paper.get("journal") or {}
        if isinstance(journal_info, dict):
            venue = journal_info.get("name") or journal_name
        else:
            venue = journal_name

        return Article(
            title=title,
            authors=authors,
            abstract=abstract,
            published=pub_date,
            source_type=SourceType.top_journal,
            doi=doi,
            arxiv_id=arxiv_id,
            s2_id=s2_id,
            html_url=url,
            pdf_url=pdf_url,
            venue=venue,
            raw=paper,
        )

    def _enrich_openalex_metadata(self, articles: List[Article]) -> None:
        email = self.openalex_config.email
        base_url = self.openalex_config.base_url
        if not email:
            return

        for article in articles:
            if not article.doi:
                continue
            try:
                params = {"filter": f"doi:{article.doi}", "mailto": email}
                resp = http_client.get(f"{base_url}/works", params=params)
                resp.raise_for_status()
                results = resp.json().get("results", [])
                if results:
                    work = results[0]
                    if not article.openalex_id:
                        article.openalex_id = work.get("id")
                    source = work.get("primary_location", {}) or {}
                    source_obj = source.get("source") or {}
                    if source_obj and not article.venue:
                        article.venue = source_obj.get("display_name")
            except Exception:
                continue
