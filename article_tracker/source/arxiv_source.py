from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, List, Optional

import feedparser
from dateutil import parser as dtp

from article_tracker.config.config_schema import ArxivSourceConfig, FreshnessConfig
from article_tracker.infra import http_client
from article_tracker.models.article import Article, SourceType
from article_tracker.source.base import BaseSource

ARXIV_HTTPS = "https://export.arxiv.org/api/query"
ARXIV_HTTP = "http://export.arxiv.org/api/query"

CONF_PAT = re.compile(
    r'\b('
    r'CVPR|ICCV|ECCV|NeurIPS|NIPS|ICLR|ICML|AAAI|IJCAI|ACL|EMNLP|NAACL|COLING|'
    r'KDD|WWW|WSDM|SIGIR|SIGGRAPH|ICME|ICASSP|WACV|ACM\s*MM|MICCAI|ISBI|CoRL|RSS|IROS|ICRA'
    r')\b(?:\s*20\d{2})?',
    flags=re.IGNORECASE,
)
ROLE_PAT = re.compile(
    r'\b(Oral|Spotlight|Poster|Highlight|Long|Short|Best\s*Paper|Honorable\s*Mention)\b',
    re.IGNORECASE,
)
URL_PAT = re.compile(r'https?://[^\s)\]>\'"]+', re.IGNORECASE)
CODE_HOSTS = (
    'github.com', 'gitlab.com', 'bitbucket.org', 'codeberg.org',
    'huggingface.co', 'gitee.com', 'sourceforge.net',
)
TRAILING_CHARS = '.,;:?!)]}>\'"'


def _clean_url(u: str) -> str:
    while u and u[-1] in TRAILING_CHARS:
        u = u[:-1]
    return u


def _is_code_url(u: str) -> bool:
    from urllib.parse import urlparse
    h = urlparse(u).netloc.lower()
    if h.startswith('www.'):
        h = h[4:]
    return any(h == ch or h.endswith('.' + ch) for ch in CODE_HOSTS)


def _extract_venue(text: str) -> Optional[str]:
    if not text:
        return None
    m = CONF_PAT.search(text)
    if not m:
        return None
    conf = m.group(0).strip()
    mr = ROLE_PAT.search(text)
    return f"{conf}{(' ' + mr.group(0).strip()) if mr else ''}"


def _extract_code_urls(text: str) -> List[str]:
    raw = URL_PAT.findall(text or "")
    urls = [_clean_url(u) for u in raw if u and _is_code_url(u)]
    seen, out = set(), []
    for u in urls:
        lk = u.lower()
        if lk not in seen:
            seen.add(lk)
            out.append(u)
    return out


def build_search_query(
    categories: List[str], keywords: List[str],
    exclude_keywords: List[str] = None, logic: str = "AND",
) -> str:
    def _quote(t: str) -> str:
        t = t.strip()
        if re.search(r'[\s-]', t):
            return f'"{t}"'
        return t

    fields = ("ti", "abs", "co")

    def _field_or(term: str) -> str:
        q = _quote(term)
        return "(" + " OR ".join(f"{f}:{q}" for f in fields) + ")"

    def _kw_group(kw: str) -> str:
        k = kw.strip()
        variants = {k}
        if " " in k:
            variants.add(k.replace(" ", "-"))
        if "-" in k:
            variants.add(k.replace("-", " "))
        parts = [_field_or(v) for v in sorted(variants, key=len, reverse=True)]
        return "(" + " OR ".join(parts) + ")"

    cats = [c.strip() for c in (categories or []) if c and c.strip()]
    keys = [k.strip() for k in (keywords or []) if k and k.strip()]
    excs = [e.strip() for e in (exclude_keywords or []) if e and e.strip()]

    cat_q = "(" + " OR ".join(f"cat:{c}" for c in cats) + ")" if cats else ""
    key_q = "(" + " OR ".join(_kw_group(k) for k in keys) + ")" if keys else ""
    exc_q = " AND NOT (" + " OR ".join(_kw_group(e) for e in excs) + ")" if excs else ""

    if cat_q and key_q:
        op = "AND" if (logic or "AND").upper() == "AND" else "OR"
        positive_q = f"({cat_q} {op} {key_q})"
    elif cat_q:
        positive_q = cat_q
    elif key_q:
        positive_q = key_q
    else:
        positive_q = "all:*"

    return positive_q + exc_q


def _parse_feed_entry(e: Any) -> Optional[Article]:
    title = (e.get("title") or "").replace("\n", " ").strip()
    if not title:
        return None
    authors = [a.get("name", "") for a in e.get("authors", [])] if "authors" in e else []
    published = e.get("published")
    updated = e.get("updated")
    published_iso = dtp.parse(published).isoformat() if published else None
    updated_iso = dtp.parse(updated).isoformat() if updated else None

    html_url = pdf_url = None
    for link in e.get("links", []):
        if link.get("rel") == "alternate":
            html_url = link.get("href")
        if link.get("title", "").lower() == "pdf" or link.get("type") == "application/pdf":
            pdf_url = link.get("href")

    entry_id = e.get("id", "")
    arxiv_id = entry_id.split("/abs/")[-1] if "/abs/" in entry_id else None
    comments = getattr(e, "arxiv_comment", None) or ""
    journal_ref = getattr(e, "arxiv_journal_ref", None)
    primary_cat = getattr(getattr(e, "arxiv_primary_category", {}), "term", None) or None
    categories = [t.get("term") for t in e.get("tags", []) if t.get("term")]
    summary = getattr(e, "summary", "")
    venue = _extract_venue(f"{comments} {journal_ref or ''}")
    code_urls = _extract_code_urls(f"{comments}\n{summary}")

    return Article(
        title=title,
        authors=authors,
        abstract=summary,
        published=published_iso,
        updated=updated_iso,
        source_type=SourceType.arxiv,
        arxiv_id=arxiv_id,
        html_url=html_url,
        pdf_url=pdf_url,
        code_links=code_urls,
        venue=venue,
        journal_ref=journal_ref,
        categories=categories,
        primary_category=primary_cat,
        comments=comments,
    )


class ArxivSource(BaseSource):
    def __init__(self, config: ArxivSourceConfig, freshness: FreshnessConfig):
        self.config = config
        self.freshness = freshness

    @property
    def name(self) -> str:
        return "arxiv"

    def fetch(self, since: date | None = None) -> List[Article]:
        query = build_search_query(
            self.config.categories, self.config.keywords,
            self.config.exclude_keywords, self.config.logic,
        )
        since = since or (date.today() - timedelta(days=self.freshness.since_days))
        since_dt = datetime(since.year, since.month, since.day)

        all_articles: List[Article] = []
        start = 0
        page_size = min(self.config.max_results, 200)

        while start < self.config.max_results:
            remaining = self.config.max_results - start
            batch = min(page_size, remaining)
            params = {
                "search_query": query,
                "start": str(start),
                "max_results": str(batch),
                "sortBy": self.config.sort_by,
                "sortOrder": self.config.sort_order,
            }
            last_err = None
            for base in (ARXIV_HTTPS, ARXIV_HTTP):
                try:
                    resp = http_client.get(base, params=params)
                    resp.raise_for_status()
                    feed = feedparser.parse(resp.text)
                    entries = feed.entries
                    break
                except Exception as e:
                    last_err = e
                    continue
            else:
                if last_err:
                    raise last_err
                break

            if not entries:
                break

            for e in entries:
                article = _parse_feed_entry(e)
                if article is None:
                    continue
                if article.published:
                    try:
                        pub_dt = dtp.parse(article.published).replace(tzinfo=None)
                        if pub_dt < since_dt:
                            continue
                    except Exception:
                        pass
                all_articles.append(article)

            start += len(entries)
            if len(entries) < batch:
                break

        return all_articles
