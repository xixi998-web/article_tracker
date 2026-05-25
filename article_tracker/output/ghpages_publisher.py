from __future__ import annotations

import html as html_mod
from datetime import datetime
from pathlib import Path
from typing import List

from article_tracker.config.config_schema import GhPagesConfig
from article_tracker.models.article import Article, ScreeningTier


def _esc(x):
    return html_mod.escape(x or "", quote=True)


_CSS = """<style>
:root{--bg:#f8fafc;--card:#fff;--text:#0f172a;--muted:#667085;--border:#e5e7eb;--acc:#2563eb;--radius:14px;--shadow:0 1px 3px rgba(0,0,0,.06)}
[data-theme="dark"]{--bg:#0b0f17;--card:#111827;--text:#e5e7eb;--muted:#9ca3af;--border:#1f2937;--shadow:0 1px 3px rgba(0,0,0,.3)}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;background:var(--bg);color:var(--text);line-height:1.6}
.container{max-width:900px;margin:0 auto;padding:20px}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px}
.header h2{font-size:22px}
.header-right{display:flex;gap:8px;align-items:center}
.btn{padding:6px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--text);cursor:pointer;font-size:13px;font-family:inherit}
.btn:hover{border-color:var(--acc);color:var(--acc)}
.badge{font-size:12px;color:var(--muted);background:var(--card);padding:4px 10px;border-radius:999px;border:1px solid var(--border)}
.tier-badge{font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;margin-left:6px}
.tier-core{background:#dbeafe;color:#1d4ed8}
.tier-proxy{background:#fef3c7;color:#92400e}
.tier-eco{background:#d1fae5;color:#065f46}
.tier-noise{background:#f3f4f6;color:#6b7280}
[data-theme="dark"] .tier-core{background:#1e3a5f;color:#93c5fd}
[data-theme="dark"] .tier-proxy{background:#422006;color:#fbbf24}
[data-theme="dark"] .tier-eco{background:#064e3b;color:#6ee7b7}
[data-theme="dark"] .tier-noise{background:#374151;color:#9ca3af}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px;margin-bottom:12px;box-shadow:var(--shadow)}
.title{font-size:17px;font-weight:700;margin-bottom:6px}
.title a{color:var(--text);text-decoration:none}
.title a:hover{color:var(--acc)}
.meta{font-size:13px;color:var(--muted);margin-bottom:4px}
.links{margin:8px 0;font-size:13px}
.links a{color:var(--acc);text-decoration:none;margin-right:10px}
.links a:hover{text-decoration:underline}
details{margin-top:6px}
summary{cursor:pointer;font-size:13px;color:var(--muted);font-weight:600;padding:4px 0;user-select:none}
summary:hover{color:var(--acc)}
.detail-body{font-size:14px;white-space:pre-wrap;margin-top:4px;padding:8px 12px;background:var(--bg);border-radius:8px;border:1px solid var(--border);font-family:inherit}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px}
.history{margin-top:24px;border-top:1px solid var(--border);padding-top:16px}
.history h3{font-size:16px;margin-bottom:8px}
.history a{color:var(--acc);text-decoration:none;font-size:14px;display:inline-block;margin:2px 8px 2px 0}
.history a:hover{text-decoration:underline}
.stats{font-size:12px;color:var(--muted);margin-bottom:12px}
</style>"""

_JS = """<script>
(function(){
  const s=localStorage.getItem('pt-theme')||'auto';
  function apply(t){
    if(t==='auto')document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme',t);
  }
  apply(s);
  window.toggleTheme=function(){
    const cur=localStorage.getItem('pt-theme')||'auto';
    const next={light:'dark',dark:'auto',auto:'light'}[cur];
    localStorage.setItem('pt-theme',next);apply(next);
    document.getElementById('theme-btn').textContent='Theme: '+next;
  };
  window.expandAll=function(){document.querySelectorAll('details').forEach(d=>d.open=true)};
  window.collapseAll=function(){document.querySelectorAll('details').forEach(d=>d.open=false)};
})();
</script>"""


def _card(a: Article) -> str:
    tier = a.screening_tier.value if a.screening_tier else ""
    tier_cls = f"tier-{tier}" if tier else ""
    title_link = f'<a href="{_esc(a.html_url or "")}">{_esc(a.title)}</a>' if a.html_url else _esc(a.title)

    parts = [f'<div class="card"><div class="title">{title_link}']
    if tier:
        parts.append(f'<span class="tier-badge {tier_cls}">{tier.upper()}</span>')
    parts.append('</div>')

    metas = []
    if a.authors:
        metas.append(f'Authors: {_esc(", ".join(a.authors[:5]))}{"..." if len(a.authors) > 5 else ""}')
    if a.venue:
        metas.append(f'Venue: {_esc(a.venue)}')
    if a.published:
        metas.append(f'Published: {a.published[:10]}')
    for m in metas:
        parts.append(f'<div class="meta">{m}</div>')

    links = []
    if a.html_url:
        links.append(f'<a href="{_esc(a.html_url)}">Abs</a>')
    if a.pdf_url:
        links.append(f'<a href="{_esc(a.pdf_url)}">PDF</a>')
    for i, u in enumerate(a.code_links[:3]):
        links.append(f'<a href="{_esc(u)}">Code{i+1}</a>')
    if links:
        parts.append(f'<div class="links">{" · ".join(links)}</div>')

    if a.abstract:
        parts.append(f'<details><summary>Abstract</summary><div class="detail-body mono">{_esc(a.abstract)}</div></details>')
    if a.digest_en:
        parts.append(f'<details><summary>Summary</summary><div class="detail-body">{_esc(a.digest_en)}</div></details>')
    if a.digest_zh:
        parts.append(f'<details><summary>总结</summary><div class="detail-body">{_esc(a.digest_zh)}</div></details>')
    if a.title_zh:
        parts.append(f'<details><summary>中文标题</summary><div class="detail-body">{_esc(a.title_zh)}</div></details>')

    parts.append('</div>')
    return "\n".join(parts)


def _build_page(articles: List[Article], today: str, history_links: str, accent: str, stats_text: str) -> str:
    cards = "\n".join(_card(a) for a in articles)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paper Tracker — {today}</title>
<style>:root{{--acc:{accent}}}</style>
{_CSS}
</head>
<body>
<div class="container">
<div class="header">
<h2>Paper Tracker</h2>
<div class="header-right">
<span class="badge">{today} · {stats_text}</span>
<button class="btn" id="theme-btn" onclick="toggleTheme()">Theme: {(lambda:localStorage.getItem('pt-theme')or'auto')()}</button>
<button class="btn" onclick="expandAll()">Expand</button>
<button class="btn" onclick="collapseAll()">Collapse</button>
</div>
</div>
{cards}
<div class="history">
<h3>History</h3>
{history_links}
</div>
</div>
{_JS}
</body>
</html>"""


def publish_ghpages(articles: List[Article], config: GhPagesConfig) -> str | None:
    if not config.enabled:
        return None
    out = Path(config.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / ".nojekyll").touch(exist_ok=True)

    archive = out / "archive"
    archive.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    tier_counts = {"core": 0, "proxy": 0, "eco": 0}
    for a in articles:
        if a.screening_tier and a.screening_tier.value in tier_counts:
            tier_counts[a.screening_tier.value] += 1
    stats_text = f"Core {tier_counts['core']} · Proxy {tier_counts['proxy']} · Eco {tier_counts['eco']}"

    archive_files = sorted(archive.glob("*.html"), key=lambda p: p.name, reverse=True)
    history_links = " · ".join(
        f'<a href="archive/{af.name}">{af.stem}</a>' for af in archive_files[:config.keep_runs]
    )

    html = _build_page(articles, today, history_links, config.accent, stats_text)
    (out / "index.html").write_text(html, encoding="utf-8")
    (archive / f"{today}.html").write_text(html, encoding="utf-8")

    while len(list(archive.glob("*.html"))) > config.keep_runs:
        oldest = sorted(archive.glob("*.html"), key=lambda p: p.name)[0]
        oldest.unlink()

    return str(out)
