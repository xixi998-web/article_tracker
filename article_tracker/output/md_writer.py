from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from article_tracker.models.article import Article


def write_markdown(articles: List[Article], out_dir: str, prefix: str = "papers") -> str:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = d / f"{prefix}_{ts}.md"

    lines = [f"# Paper Tracker Report — {datetime.now().strftime('%Y-%m-%d')}\n"]
    tier_groups: dict[str, List[Article]] = {}
    for a in articles:
        tier = a.screening_tier.value if a.screening_tier else "unclassified"
        tier_groups.setdefault(tier, []).append(a)

    for tier in ("core", "proxy", "eco", "noise"):
        group = tier_groups.get(tier, [])
        if not group:
            continue
        lines.append(f"\n## {tier.upper()} ({len(group)})\n")
        for i, a in enumerate(group, 1):
            lines.append(f"### {i}. {a.title}")
            if a.authors:
                lines.append(f"- **Authors**: {', '.join(a.authors[:5])}{'...' if len(a.authors) > 5 else ''}")
            if a.venue:
                lines.append(f"- **Venue**: {a.venue}")
            if a.published:
                lines.append(f"- **Published**: {a.published}")
            if a.doi:
                lines.append(f"- **DOI**: {a.doi}")
            if a.abstract:
                lines.append(f"- **Abstract**: {a.abstract[:300]}{'...' if len(a.abstract) > 300 else ''}")
            if a.digest_zh:
                lines.append(f"- **总结**: {a.digest_zh}")
            elif a.digest_en:
                lines.append(f"- **Summary**: {a.digest_en}")
            links = []
            if a.html_url:
                links.append(f"[Abs]({a.html_url})")
            if a.pdf_url:
                links.append(f"[PDF]({a.pdf_url})")
            for j, u in enumerate(a.code_links[:3]):
                links.append(f"[Code{j+1}]({u})")
            if links:
                lines.append(f"- **Links**: {' | '.join(links)}")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
