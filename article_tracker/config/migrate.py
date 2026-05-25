from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml


def migrate_arxiv_config(arxiv_config_path: str, output_path: str) -> Dict[str, Any]:
    p = Path(arxiv_config_path)
    if not p.exists():
        raise FileNotFoundError(f"Arxiv config not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        old = yaml.safe_load(f) or {}

    unified = {
        "arxiv": {
            "enabled": True,
            "categories": old.get("categories", []),
            "keywords": old.get("keywords", []),
            "exclude_keywords": old.get("exclude_keywords", []),
            "logic": old.get("logic", "AND"),
            "max_results": old.get("max_results", 50),
            "sort_by": old.get("sort_by", "submittedDate"),
            "sort_order": old.get("sort_order", "descending"),
        },
        "top_journal": {"enabled": False},
        "freshness": {"since_days": 7},
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        yaml.dump(unified, f, allow_unicode=True, default_flow_style=False)
    return unified


def migrate_frontier_state(state_path: str, seen_path: str) -> int:
    p = Path(state_path)
    if not p.exists():
        return 0
    with open(p, "r", encoding="utf-8") as f:
        old_state = json.load(f)

    seen: Dict[str, Any] = {}
    if Path(seen_path).exists():
        with open(seen_path, "r", encoding="utf-8") as f:
            seen = json.load(f)

    count = 0
    for paper_id, info in old_state.items():
        if isinstance(info, dict):
            doi = info.get("doi")
            key = f"doi:{doi.lower()}" if doi else f"openalex:{paper_id}"
            if key not in seen:
                seen[key] = info
                count += 1

    Path(seen_path).parent.mkdir(parents=True, exist_ok=True)
    with open(seen_path, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)
    return count
