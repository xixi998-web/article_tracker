from __future__ import annotations

import logging
from typing import List

from article_tracker.models.article import Article, ScreeningTier
from article_tracker.models.profile import ResearchProfile
from article_tracker.screen.profile_loader import ProfileLoader

logger = logging.getLogger(__name__)


class TierClassifier:
    def __init__(self, profile: ResearchProfile, output_tiers: List[str] | None = None):
        self.profile = profile
        self.output_tiers = [ScreeningTier(t) for t in (output_tiers or ["core", "proxy", "eco"])]

    @classmethod
    def from_file(cls, path: str | None, output_tiers: List[str] | None = None) -> "TierClassifier":
        if path:
            profile = ProfileLoader.load(path)
            return cls(profile, output_tiers)
        return cls(ResearchProfile(
            core_keywords=["*"], proxy_keywords=[], eco_keywords=[], exclusion_keywords=[]
        ), output_tiers)

    @classmethod
    def from_config(cls, screening_config, output_tiers: List[str] | None = None) -> "TierClassifier":
        if screening_config.core_keywords:
            profile = ResearchProfile(
                core_keywords=screening_config.core_keywords or ["*"],
                proxy_keywords=screening_config.proxy_keywords or [],
                eco_keywords=screening_config.eco_keywords or [],
                exclusion_keywords=screening_config.exclusion_keywords or [],
                must_track_journals=screening_config.must_track_journals or [],
            )
            return cls(profile, output_tiers or screening_config.output_tiers)
        return cls.from_file(screening_config.profile_path, output_tiers or screening_config.output_tiers)

    def classify(self, articles: List[Article]) -> dict:
        stats = {"core": 0, "proxy": 0, "eco": 0, "noise": 0}
        for article in articles:
            tier = self._classify_one(article)
            article.screening_tier = tier
            stats[tier.value] += 1
        return stats

    def filter_by_tiers(self, articles: List[Article]) -> List[Article]:
        return [a for a in articles if a.screening_tier in self.output_tiers]

    def _classify_one(self, article: Article) -> ScreeningTier:
        text = f"{article.title} {article.abstract or ''}".lower()

        if self._matches_any(text, self.profile.exclusion_keywords):
            return ScreeningTier.noise

        if self._matches_journal(article):
            return ScreeningTier.core

        if self._matches_any(text, self.profile.core_keywords):
            return ScreeningTier.core
        if self._matches_any(text, self.profile.proxy_keywords):
            return ScreeningTier.proxy
        if self._matches_any(text, self.profile.eco_keywords):
            return ScreeningTier.eco

        return ScreeningTier.noise

    def _matches_any(self, text: str, keywords: List[str]) -> bool:
        for kw in keywords:
            if kw == "*":
                return True
            if kw.lower() in text:
                return True
        return False

    def _matches_journal(self, article: Article) -> bool:
        venue = (article.venue or "").lower()
        for j in self.profile.must_track_journals:
            if j.lower() in venue:
                return True
        return False
