from __future__ import annotations

import logging
import re
from typing import List

from article_tracker.config.config_schema import S2Config
from article_tracker.infra import http_client
from article_tracker.models.article import Article

logger = logging.getLogger(__name__)

_CODE_HOSTS = r"(?:github\.com|gitlab\.com|huggingface\.co|gitee\.com)"
_URL_TAIL = r'[^\s\]\)\<\>"\'\u3002\uFF0C\uFF1B\u3001]+'
_RE_CODE_URL = re.compile(rf"https?://{_CODE_HOSTS}/{_URL_TAIL}", re.I)

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)


class CodeLinkEnricher:
    def __init__(self, s2_config: S2Config, timeout: int = 10):
        self.s2_config = s2_config
        self.timeout = timeout

    def enrich(self, articles: List[Article]) -> dict:
        stats = {"structured": 0, "scraped": 0, "total_new": 0}
        for article in articles:
            before = len(article.code_links)
            self._from_metadata(article)
            if len(article.code_links) > before:
                stats["structured"] += len(article.code_links) - before
            if article.html_url:
                scraped = self._scrape_html(article.html_url)
                new_urls = [u for u in scraped if u not in article.code_links]
                article.code_links.extend(new_urls)
                stats["scraped"] += len(new_urls)
            stats["total_new"] += len(article.code_links) - before
        return stats

    def _from_metadata(self, article: Article) -> None:
        if article.raw and isinstance(article.raw, dict):
            for key in ("githubUrls", "url"):
                urls = article.raw.get(key)
                if isinstance(urls, list):
                    for u in urls:
                        if isinstance(u, str) and self._is_code_url(u) and u not in article.code_links:
                            article.code_links.append(u)
                elif isinstance(urls, str) and self._is_code_url(urls) and urls not in article.code_links:
                    article.code_links.append(urls)
        text = f"{article.abstract or ''}\n{article.comments or ''}\n{article.title or ''}"
        for u in self._extract_from_text(text):
            if u not in article.code_links:
                article.code_links.append(u)

    def _scrape_html(self, url: str) -> List[str]:
        try:
            resp = http_client.get(url, headers={"User-Agent": UA}, timeout=self.timeout)
            resp.raise_for_status()
            return self._extract_from_text(resp.text)
        except Exception:
            return []

    def _extract_from_text(self, text: str) -> List[str]:
        raw = _RE_CODE_URL.findall(text or "")
        urls = [u.rstrip('.,;:)]}>\'"，。；：）】》') for u in raw]
        seen, out = set(), []
        for u in urls:
            lk = u.lower()
            if lk not in seen:
                seen.add(lk)
                out.append(u)
        return out

    @staticmethod
    def _is_code_url(url: str) -> bool:
        return bool(re.match(r"https?://(github\.com|gitlab\.com|huggingface\.co|gitee\.com)/", url, re.I))
