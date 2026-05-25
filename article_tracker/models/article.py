from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    arxiv = "arxiv"
    top_journal = "top_journal"


class ScreeningTier(str, Enum):
    core = "core"
    proxy = "proxy"
    eco = "eco"
    noise = "noise"


class AbstractSource(str, Enum):
    original = "original"
    semantic_scholar = "semantic_scholar"
    openalex = "openalex"
    crossref = "crossref"
    llm = "llm"
    none_ = "none"


class Identifier(BaseModel):
    type: str
    value: str


class Article(BaseModel):
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str = ""
    abstract_source: AbstractSource = AbstractSource.original
    published: Optional[str] = None
    updated: Optional[str] = None
    source_type: SourceType
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    openalex_id: Optional[str] = None
    s2_id: Optional[str] = None
    identifiers: List[Identifier] = Field(default_factory=list)
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    code_links: List[str] = Field(default_factory=list)
    project_urls: List[str] = Field(default_factory=list)
    other_urls: List[str] = Field(default_factory=list)
    venue: Optional[str] = None
    journal_ref: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    primary_category: Optional[str] = None
    comments: Optional[str] = None
    screening_tier: Optional[ScreeningTier] = None
    digest_en: Optional[str] = None
    digest_zh: Optional[str] = None
    title_zh: Optional[str] = None
    abstract_zh: Optional[str] = None
    raw: dict = Field(default_factory=dict, exclude=True)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v

    @property
    def dedup_key_doi(self) -> Optional[str]:
        return self.doi.strip().lower() if self.doi else None

    @property
    def dedup_key_arxiv(self) -> Optional[str]:
        return self.arxiv_id.strip().lower() if self.arxiv_id else None

    @property
    def dedup_key_title(self) -> str:
        from article_tracker.utils.text import normalize_title
        return normalize_title(self.title)
