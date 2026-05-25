from __future__ import annotations

from difflib import SequenceMatcher


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def is_similar(a: str, b: str, threshold: float = 0.85) -> bool:
    return similarity(a, b) >= threshold


def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())
