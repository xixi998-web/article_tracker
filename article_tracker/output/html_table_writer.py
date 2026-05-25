from __future__ import annotations

import html as html_mod
from datetime import datetime
from pathlib import Path
from typing import List

from article_tracker.models.article import Article


def _esc(x):
    return html_mod.escape(x or "", quote=True)


def write_html_table(articles: List[Article], out_dir: str, prefix: str = "papers") -> str:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = d / f"{prefix}_{ts}.html"

    rows = []
    for a in articles:
        tier = a.screening_tier.value if a.screening_tier else ""
        links = []
        if a.html_url:
            links.append(f'<a href="{_esc(a.html_url)}" target="_blank">Abs</a>')
        if a.pdf_url:
            links.append(f'<a href="{_esc(a.pdf_url)}" target="_blank">PDF</a>')
        for i, u in enumerate(a.code_links[:2]):
            links.append(f'<a href="{_esc(u)}" target="_blank">Code{i+1}</a>')
        rows.append(
            f'<tr><td>{_esc(a.title)}</td><td>{_esc(", ".join(a.authors[:3]))}</td>'
            f'<td>{_esc(a.venue or "")}</td><td>{tier}</td>'
            f'<td>{_esc(a.published or "")}</td>'
            f'<td>{" · ".join(links)}</td></tr>'
        )

    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Paper Tracker</title>
<style>body{{font-family:ui-sans-serif,system-ui;max-width:1200px;margin:0 auto;padding:18px}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #e5e7eb;padding:8px;text-align:left}}
th{{background:#f8fafc;cursor:pointer}}tr:hover{{background:#f0f4f8}}</style>
<script>function sortTable(n){{var t=document.getElementsByTagName("table")[0],rows=Array.from(t.rows).slice(1);
rows.sort((a,b)=>a.cells[n].textContent.localeCompare(b.cells[n].textContent));
var b=t.getElementsByTagName("tbody")[0];b.innerHTML="";rows.forEach(r=>b.appendChild(r))}}</script>
</head><body><h2>Paper Tracker — {datetime.now().strftime("%Y-%m-%d")} ({len(articles)} papers)</h2>
<input type="text" id="search" placeholder="Search..." oninput="filterTable(this.value)" style="margin:8px 0;padding:6px;width:300px">
<table><thead><tr><th onclick="sortTable(0)">Title</th><th onclick="sortTable(1)">Authors</th>
<th onclick="sortTable(2)">Venue</th><th onclick="sortTable(3)">Tier</th>
<th onclick="sortTable(4)">Published</th><th>Links</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
<script>function filterTable(q){{var rows=document.querySelectorAll("tbody tr");q=q.toLowerCase();
rows.forEach(r=>{{var t=r.textContent.toLowerCase();r.style.display=t.includes(q)?"":"none"}})}}</script>
</body></html>"""

    path.write_text(html, encoding="utf-8")
    return str(path)
