from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from article_tracker.models.article import Article


def write_obsidian(articles: List[Article], vault_path: str) -> int:
    vault = Path(vault_path)
    vault.mkdir(parents=True, exist_ok=True)
    count = 0
    for a in articles:
        tier = a.screening_tier.value if a.screening_tier else ""
        slug = a.title[:80].replace("/", "-").replace(":", "-").replace('"', "").strip()
        path = vault / f"{slug}.md"
        frontmatter = [
            "---",
            f"title: \"{a.title}\"",
            f"authors: [{', '.join(repr(x) for x in a.authors[:5])}]",
            f"venue: \"{a.venue or ''}\"",
            f"published: \"{a.published or ''}\"",
            f"doi: \"{a.doi or ''}\"",
            f"tier: \"{tier}\"",
            f"source: \"{a.source_type.value}\"",
            f"tracked: \"{datetime.now().strftime('%Y-%m-%d')}\"",
            "---",
        ]
        body = [f"# {a.title}\n"]
        if a.abstract:
            body.append(f"## Abstract\n\n{a.abstract}\n")
        if a.digest_zh:
            body.append(f"## 总结\n\n{a.digest_zh}\n")
        elif a.digest_en:
            body.append(f"## Summary\n\n{a.digest_en}\n")
        links = []
        if a.html_url:
            links.append(f"- Abs: {a.html_url}")
        if a.pdf_url:
            links.append(f"- PDF: {a.pdf_url}")
        for u in a.code_links[:3]:
            links.append(f"- Code: {u}")
        if links:
            body.append("## Links\n" + "\n".join(links) + "\n")

        path.write_text("\n".join(frontmatter) + "\n" + "\n".join(body), encoding="utf-8")
        count += 1
    return count
