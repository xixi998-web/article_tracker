from __future__ import annotations

import html as html_mod
from datetime import datetime
from pathlib import Path
from typing import List

from article_tracker.config.config_schema import GhPagesConfig
from article_tracker.models.article import Article


def _esc(x):
    return html_mod.escape(x or "", quote=True)


_CSS = """<style>
:root{--bg:#f8fafc;--card:#ffffff;--text:#0f172a;--muted:#667085;--border:#e5e7eb;--acc:#2563eb}
:root[data-theme="dark"]{--bg:#0b0f17;--card:#111827;--text:#e5e7eb;--muted:#9ca3af;--border:#1f2937;--acc:#2563eb}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;line-height:1.6}
.container{max-width:900px;margin:0 auto;padding:18px}
.header{display:flex;gap:10px;justify-content:space-between;align-items:center;margin:8px 0 16px;flex-wrap:wrap}
h1{font-size:22px;margin:0}
.badge{font-size:12px;color:#111827;background:var(--acc);padding:2px 8px;border-radius:999px}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px 18px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.title{font-weight:700;margin:0 0 6px 0;font-size:18px}
.meta-line{color:var(--muted);font-size:13px;margin:2px 0}
.links a{color:var(--acc);text-decoration:none;margin-right:12px}
.links a:hover{text-decoration:underline}
.detail{margin-top:10px;background:rgba(2,6,23,.03);border:1px solid var(--border);border-radius:10px;padding:8px 10px}
summary{cursor:pointer;color:var(--acc)}
.mono{white-space:pre-wrap;background:rgba(2,6,23,.03);border:1px solid var(--border);padding:10px;border-radius:10px}
.tier-badge{font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;margin-left:6px}
.tier-core{background:#dbeafe;color:#1d4ed8}
.tier-proxy{background:#fef3c7;color:#92400e}
.tier-eco{background:#d1fae5;color:#065f46}
.tier-noise{background:#f3f4f6;color:#6b7280}
[data-theme="dark"] .tier-core{background:#1e3a5f;color:#93c5fd}
[data-theme="dark"] .tier-proxy{background:#422006;color:#fbbf24}
[data-theme="dark"] .tier-eco{background:#064e3b;color:#6ee7b7}
[data-theme="dark"] .tier-noise{background:#374151;color:#9ca3af}
.controls{display:flex;gap:8px;align-items:center}
.btn{border:1px solid var(--border);background:var(--card);padding:6px 10px;border-radius:10px;cursor:pointer;color:var(--text)}
.btn:hover{border-color:var(--acc)}
.hr{height:1px;background:var(--border);margin:14px 0}
.history-list a{display:block;color:var(--acc);text-decoration:none;margin:4px 0}
.history-list a:hover{text-decoration:underline}
.footer{color:var(--muted);font-size:13px;margin:20px 0 10px}
</style>"""

_JS = """<script>
(function(){
  var root=document.documentElement;
  function apply(t){
    if(t==='dark')root.setAttribute('data-theme','dark');
    else if(t==='light')root.removeAttribute('data-theme');
    else{
      if(window.matchMedia&&window.matchMedia('(prefers-color-scheme:dark)').matches)
        root.setAttribute('data-theme','dark');
      else root.removeAttribute('data-theme');
    }
  }
  var t=localStorage.getItem('theme')||'light';
  if(!['light','dark','auto'].includes(t))t='light';
  apply(t);
  window.__toggleTheme=function(){
    var cur=localStorage.getItem('theme')||'light';
    if(cur==='light')cur='dark';
    else if(cur==='dark')cur='auto';
    else cur='light';
    localStorage.setItem('theme',cur);apply(cur);
    var el=document.getElementById('theme-label');
    if(el)el.textContent=cur.toUpperCase();
  };
  window.__expandAll=function(open){
    document.querySelectorAll('details').forEach(function(d){d.open=!!open});
  };
})();
</script>"""


def _card(a: Article) -> str:
    tier = a.screening_tier.value if a.screening_tier else ""
    tier_cls = f"tier-{tier}" if tier else ""
    tier_badge = f'<span class="tier-badge {tier_cls}">{tier.upper()}</span>' if tier else ""
    fallback_badge = '<span class="tier-badge tier-noise" style="margin-left:4px">FALLBACK</span>' if a.is_fallback else ""

    parts = [f'<div class="card"><div class="title">{_esc(a.title)}{tier_badge}{fallback_badge}</div>']

    if a.authors:
        parts.append(f'<div class="meta-line">Authors: {_esc(", ".join(a.authors[:5]))}{"..." if len(a.authors) > 5 else ""}</div>')
    if a.venue:
        parts.append(f'<div class="meta-line">Venue: {_esc(a.venue)}</div>')
    if a.published:
        parts.append(f'<div class="meta-line">Published: {a.published[:10]}</div>')

    links = []
    if a.html_url:
        links.append(f'<a href="{_esc(a.html_url)}">Abs</a>')
    if a.pdf_url:
        links.append(f'<a href="{_esc(a.pdf_url)}">PDF</a>')
    for i, u in enumerate(a.code_links[:3]):
        links.append(f'<a href="{_esc(u)}">Code{i+1}</a>')
    if links:
        parts.append(f'<div class="links" style="margin-top:8px">{" · ".join(links)}</div>')

    if a.abstract:
        parts.append(f'<details class="detail"><summary>Abstract</summary><div class="mono">{_esc(a.abstract)}</div></details>')

    if a.digest_en or a.digest_zh:
        parts.append('<details class="detail"><summary>Summary / 总结</summary>')
        if a.digest_en:
            parts.append(f'<div class="mono">{_esc(a.digest_en)}</div>')
        if a.digest_zh:
            parts.append(f'<div class="mono" style="margin-top:8px">{_esc(a.digest_zh)}</div>')
        parts.append('</details>')

    if a.title_zh:
        parts.append(f'<details class="detail"><summary>中文标题</summary><div class="mono">{_esc(a.title_zh)}</div></details>')

    parts.append('</div>')
    return "\n".join(parts)


def _build_page(articles: List[Article], now_str: str, history_links: str, accent: str, stats_text: str) -> str:
    cards = "\n".join(_card(a) for a in articles)
    controls = """
<div class="controls">
  <button class="btn" onclick="__toggleTheme()">Theme: <span id="theme-label" style="margin-left:6px">AUTO</span></button>
  <button class="btn" onclick="__expandAll(true)">Expand All</button>
  <button class="btn" onclick="__expandAll(false)">Collapse All</button>
</div>"""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paper Tracker</title>
<style>:root{{--acc:{accent}}}</style>
{_CSS}
</head>
<body>
<div class="container">
<div class="header">
<h1>Paper Tracker</h1>
<div style="display:flex;gap:10px;align-items:center">
{controls}
<span class="badge">{now_str} · {stats_text}</span>
</div>
</div>
<div class="hr"></div>
<div class="row">
{cards}
</div>
<details style="margin-top:16px" class="detail"><summary>History</summary>
<div class="history-list">
{history_links}
</div>
</details>
<div class="footer">Generated by article_tracker</div>
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
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    tier_counts = {"core": 0, "proxy": 0, "eco": 0}
    for a in articles:
        if a.screening_tier and a.screening_tier.value in tier_counts:
            tier_counts[a.screening_tier.value] += 1
    stats_text = f"Core {tier_counts['core']} · Proxy {tier_counts['proxy']} · Eco {tier_counts['eco']}"

    archive_files = sorted(archive.glob("*.html"), key=lambda p: p.name, reverse=True)
    history_links = "\n".join(
        f'<a href="archive/{af.name}">{af.stem}</a>' for af in archive_files[:config.keep_runs]
    )

    html_content = _build_page(articles, now_str, history_links, config.accent, stats_text)
    (out / "index.html").write_text(html_content, encoding="utf-8")

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    (archive / f"{stamp}.html").write_text(html_content, encoding="utf-8")

    while len(list(archive.glob("*.html"))) > config.keep_runs:
        oldest = sorted(archive.glob("*.html"), key=lambda p: p.name)[0]
        oldest.unlink()

    return str(out)
