from __future__ import annotations

import html as html_mod
from datetime import datetime
from pathlib import Path
from typing import List

from article_tracker.config.config_schema import GhPagesConfig
from article_tracker.models.article import Article


def _esc(x):
    return html_mod.escape(x or "", quote=True)


def publish_ghpages(articles: List[Article], config: GhPagesConfig) -> str | None:
    if not config.enabled:
        return None
    out = Path(config.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / ".nojekyll").touch(exist_ok=True)

    archive = out / "archive"
    archive.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    cards = []
    for a in articles[:100]:
        tier = a.screening_tier.value if a.screening_tier else ""
        card = '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:14px;margin:12px 0;">'
        card += f'<div style="font-weight:700;font-size:16px;">{_esc(a.title)}</div>'
        if a.authors:
            card += f'<div style="color:#667085;font-size:13px;">Authors: {_esc(", ".join(a.authors[:5]))}</div>'
        if a.venue:
            card += f'<div style="color:#667085;font-size:13px;">Venue: {_esc(a.venue)} | Tier: {tier}</div>'
        links = []
        if a.html_url:
            links.append(f'<a href="{_esc(a.html_url)}">Abs</a>')
        if a.pdf_url:
            links.append(f'<a href="{_esc(a.pdf_url)}">PDF</a>')
        if links:
            card += f'<div style="margin:8px 0">{" · ".join(links)}</div>'
        if a.digest_en:
            card += f'<details><summary>Summary</summary><div style="white-space:pre-wrap">{_esc(a.digest_en)}</div></details>'
        if a.digest_zh:
            card += f'<details><summary>总结</summary><div style="white-space:pre-wrap">{_esc(a.digest_zh)}</div></details>'
        card += '</div>'
        cards.append(card)

    archive_files = sorted(archive.glob("*.html"), key=lambda p: p.name, reverse=True)
    history_links = ""
    for af in archive_files[:config.keep_runs]:
        history_links += f'<div><a href="archive/{af.name}">{af.stem}</a></div>'

    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paper Tracker</title></head><body>
<div style="max-width:900px;margin:0 auto;padding:18px;font-family:ui-sans-serif,system-ui;">
<h2>Paper Tracker — {today}</h2>
{''.join(cards)}
<h3>History</h3>{history_links}</div></body></html>"""

    (out / "index.html").write_text(html, encoding="utf-8")
    (archive / f"{today}.html").write_text(html, encoding="utf-8")

    while len(list(archive.glob("*.html"))) > config.keep_runs:
        oldest = sorted(archive.glob("*.html"), key=lambda p: p.name)[0]
        oldest.unlink()

    return str(out)
