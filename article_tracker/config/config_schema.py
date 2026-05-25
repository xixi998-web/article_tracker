from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ArxivSourceConfig(BaseModel):
    enabled: bool = True
    categories: List[str] = Field(default_factory=lambda: ["cs.CV", "cs.AI", "cs.LG"])
    keywords: List[str] = Field(default_factory=list)
    exclude_keywords: List[str] = Field(default_factory=list)
    logic: str = "AND"
    max_results: int = 50
    sort_by: str = "submittedDate"
    sort_order: str = "descending"


class TopJournalSourceConfig(BaseModel):
    enabled: bool = True
    watchlist_path: str = "references/top-journal-families.md"
    since_days: int = 7
    max_per_journal: int = 50


class DedupConfig(BaseModel):
    seen_path: str = ".state/seen.json"
    title_threshold: float = 0.85
    prefer_source: str = "top_journal"


class ScreeningConfig(BaseModel):
    profile_path: str = "references/research-profile.md"
    output_tiers: List[str] = Field(default_factory=lambda: ["core", "proxy", "eco"])


class LLMConfig(BaseModel):
    enabled: bool = False
    base_url: str = ""
    model: str = ""
    api_key_env: str = "DS_API_KEY"
    api_key: str = ""
    system_prompt_zh: str = ""
    system_prompt_en: str = ""
    timeout: int = 60


class EmailConfig(BaseModel):
    enabled: bool = False
    sender: str = ""
    to: List[str] = Field(default_factory=list)
    smtp_server: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_pass_env: str = "SMTP_PASS"
    smtp_pass: str = ""
    tls_mode: str = "auto"
    subject_prefix: str = "Paper Tracker"


class GhPagesConfig(BaseModel):
    enabled: bool = False
    output_dir: str = "docs"
    keep_runs: int = 30
    accent: str = "#2563eb"
    theme_mode: str = "auto"


class OutputConfig(BaseModel):
    dir: str = "outputs"
    json_enabled: bool = True
    md_enabled: bool = True
    pdf_enabled: bool = False
    excel_enabled: bool = False
    html_table_enabled: bool = True
    obsidian_enabled: bool = False
    obsidian_vault: str = ""
    zotero_enabled: bool = False
    email: EmailConfig = Field(default_factory=EmailConfig)
    ghpages: GhPagesConfig = Field(default_factory=GhPagesConfig)


class ScheduleConfig(BaseModel):
    enabled: bool = False
    cron: str = "0 3 * * *"
    timezone: str = "Asia/Shanghai"


class FreshnessConfig(BaseModel):
    since_days: int = 7
    max_age_days: int = 365


class S2Config(BaseModel):
    api_key_env: str = "S2_API_KEY"
    api_key: str = ""
    base_url: str = "https://api.semanticscholar.org/graph/v1"


class OpenAlexConfig(BaseModel):
    email_env: str = "OPENALEX_EMAIL"
    email: str = ""
    base_url: str = "https://api.openalex.org"


class UnifiedConfig(BaseModel):
    arxiv: ArxivSourceConfig = Field(default_factory=ArxivSourceConfig)
    top_journal: TopJournalSourceConfig = Field(default_factory=TopJournalSourceConfig)
    dedup: DedupConfig = Field(default_factory=DedupConfig)
    screening: ScreeningConfig = Field(default_factory=ScreeningConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    freshness: FreshnessConfig = Field(default_factory=FreshnessConfig)
    s2: S2Config = Field(default_factory=S2Config)
    openalex: OpenAlexConfig = Field(default_factory=OpenAlexConfig)
    source_filter: str = "all"
    dry_run: bool = False
    verbose: bool = False
    profile_path: Optional[str] = None
