from __future__ import annotations

import logging
from pathlib import Path

from article_tracker.models.profile import ResearchProfile

logger = logging.getLogger(__name__)


class ProfileLoader:
    @staticmethod
    def load(path: str) -> ResearchProfile:
        p = Path(path)
        if not p.exists():
            logger.warning(f"Profile not found: {path}, using empty eco-level profile")
            return ResearchProfile(
                core_keywords=["*"], proxy_keywords=[], eco_keywords=[], exclusion_keywords=[]
            )
        text = p.read_text(encoding="utf-8")
        return ProfileLoader._parse(text)

    @staticmethod
    def _parse(text: str) -> ResearchProfile:
        core, proxy, eco, exclusion = [], [], [], []
        must_journals, nice_journals = [], []
        current_section = None

        for line in text.splitlines():
            stripped = line.strip()
            lower = stripped.lower()

            if lower.startswith("## core") or lower.startswith("## core keywords") or lower.startswith("core topics"):
                current_section = "core"
            elif lower.startswith("## proxy") or lower.startswith("## proxy keywords") or lower.startswith("secondary topics"):
                current_section = "proxy"
            elif lower.startswith("## eco") or lower.startswith("## eco keywords") or lower.startswith("study systems") or lower.startswith("methods"):
                current_section = "eco"
            elif lower.startswith("## exclusion") or lower.startswith("## exclude"):
                current_section = "exclusion"
            elif lower.startswith("## must-track") or lower.startswith("must_track_journals"):
                current_section = "must_journals"
            elif lower.startswith("## nice-to-track") or lower.startswith("nice_to_track_journals"):
                current_section = "nice_journals"
            elif stripped.startswith("- ") or stripped.startswith("* "):
                kw = stripped[2:].strip().strip("`")
                if not kw:
                    continue
                if current_section == "core":
                    core.append(kw)
                elif current_section == "proxy":
                    proxy.append(kw)
                elif current_section == "eco":
                    eco.append(kw)
                elif current_section == "exclusion":
                    exclusion.append(kw)
                elif current_section == "must_journals":
                    must_journals.append(kw)
                elif current_section == "nice_journals":
                    nice_journals.append(kw)

        return ResearchProfile(
            core_keywords=core or ["*"],
            proxy_keywords=proxy,
            eco_keywords=eco,
            exclusion_keywords=exclusion,
            must_track_journals=must_journals,
            nice_to_track_journals=nice_journals,
        )
