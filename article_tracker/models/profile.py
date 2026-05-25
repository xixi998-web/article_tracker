from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator


class ResearchProfile(BaseModel):
    core_keywords: List[str] = Field(default_factory=list)
    proxy_keywords: List[str] = Field(default_factory=list)
    eco_keywords: List[str] = Field(default_factory=list)
    exclusion_keywords: List[str] = Field(default_factory=list)
    must_track_journals: List[str] = Field(default_factory=list)
    nice_to_track_journals: List[str] = Field(default_factory=list)

    @field_validator("core_keywords", "proxy_keywords", "eco_keywords")
    @classmethod
    def keywords_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("core/proxy/eco keywords must not be empty")
        return v
