from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from article_tracker.models.article import Article


def write_json(articles: List[Article], out_dir: str, prefix: str = "papers") -> str:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = d / f"{prefix}_{ts}.json"
    data = [a.model_dump(mode="json", exclude_none=True) for a in articles]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
