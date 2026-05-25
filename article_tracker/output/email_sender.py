from __future__ import annotations

import html as html_mod
import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from article_tracker.config.config_schema import EmailConfig
from article_tracker.models.article import Article

logger = logging.getLogger(__name__)

_BG = "#0b0f17"
_CARD = "#111827"
_TEXT = "#e5e7eb"
_MUTED = "#9ca3af"
_BORDER = "#1f2937"
_ACC = "#2563eb"
_RADIUS = "14px"

_TIER_STYLE = {
    "core": "background:#1e3a5f;color:#93c5fd;",
    "proxy": "background:#422006;color:#fbbf24;",
    "eco": "background:#064e3b;color:#6ee7b7;",
    "noise": "background:#374151;color:#9ca3af;",
}


def _esc(x: Optional[str]) -> str:
    return html_mod.escape(x or "", quote=True)


def _card(a: Article) -> str:
    tier = a.screening_tier.value if a.screening_tier else ""
    title_link = f'<a href="{_esc(a.html_url)}" style="color:{_TEXT};text-decoration:none;">{_esc(a.title)}</a>' if a.html_url else _esc(a.title)
    tier_badge = ""
    if tier:
        ts = _TIER_STYLE.get(tier, "")
        tier_badge = f'<span style="display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;margin-left:6px;{ts}">{tier.upper()}</span>'

    parts = [f'<div style="background:{_CARD};border:1px solid {_BORDER};border-radius:{_RADIUS};padding:16px;margin-bottom:12px;">']
    parts.append(f'<div style="font-size:17px;font-weight:700;margin-bottom:6px;">{title_link}{tier_badge}</div>')

    metas = []
    if a.authors:
        metas.append(f'Authors: {_esc(", ".join(a.authors[:5]))}{"..." if len(a.authors) > 5 else ""}')
    if a.venue:
        metas.append(f'Venue: {_esc(a.venue)}')
    if a.published:
        metas.append(f'Published: {a.published[:10]}')
    for m in metas:
        parts.append(f'<div style="font-size:13px;color:{_MUTED};margin-bottom:2px;">{m}</div>')

    links = []
    if a.html_url:
        links.append(f'<a href="{_esc(a.html_url)}" style="color:{_ACC};text-decoration:none;">Abs</a>')
    if a.pdf_url:
        links.append(f'<a href="{_esc(a.pdf_url)}" style="color:{_ACC};text-decoration:none;">PDF</a>')
    for i, u in enumerate(a.code_links[:3]):
        links.append(f'<a href="{_esc(u)}" style="color:{_ACC};text-decoration:none;">Code{i+1}</a>')
    if links:
        parts.append(f'<div style="margin:8px 0;font-size:13px;">{" &middot; ".join(links)}</div>')

    detail_box = f'font-size:14px;white-space:pre-wrap;margin-top:4px;padding:8px 12px;background:{_BG};border-radius:8px;border:1px solid {_BORDER};'
    if a.abstract:
        parts.append(f'<details><summary style="cursor:pointer;font-size:13px;color:{_MUTED};font-weight:600;">Abstract</summary><div style="{detail_box}">{_esc(a.abstract)}</div></details>')
    if a.digest_en:
        parts.append(f'<details><summary style="cursor:pointer;font-size:13px;color:{_MUTED};font-weight:600;">Summary</summary><div style="{detail_box}">{_esc(a.digest_en)}</div></details>')
    if a.digest_zh:
        parts.append(f'<details><summary style="cursor:pointer;font-size:13px;color:{_MUTED};font-weight:600;">总结</summary><div style="{detail_box}">{_esc(a.digest_zh)}</div></details>')
    if a.title_zh:
        parts.append(f'<details><summary style="cursor:pointer;font-size:13px;color:{_MUTED};font-weight:600;">中文标题</summary><div style="{detail_box}">{_esc(a.title_zh)}</div></details>')

    parts.append('</div>')
    return "\n".join(parts)


def send_email(articles: List[Article], config: EmailConfig, subject_prefix: str = "Paper Tracker") -> str | None:
    if not config.enabled:
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    tier_counts = {"core": 0, "proxy": 0, "eco": 0}
    for a in articles:
        if a.screening_tier and a.screening_tier.value in tier_counts:
            tier_counts[a.screening_tier.value] += 1
    stats_text = f"Core {tier_counts['core']} · Proxy {tier_counts['proxy']} · Eco {tier_counts['eco']}"

    cards = "\n".join(_card(a) for a in articles[:50])
    html_body = f"""<!doctype html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:{_BG};font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;color:{_TEXT};line-height:1.6;">
<div style="max-width:900px;margin:0 auto;padding:20px;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px;">
<h2 style="font-size:22px;margin:0;">{_esc(subject_prefix)}</h2>
<span style="font-size:12px;color:{_MUTED};background:{_CARD};padding:4px 10px;border-radius:999px;border:1px solid {_BORDER};">{today} · {stats_text}</span>
</div>
{cards}
</div>
</body></html>"""

    msg = MIMEMultipart()
    msg["From"] = config.sender
    msg["To"] = ", ".join(config.to)
    msg["Subject"] = f"{subject_prefix} — {today}"
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if config.tls_mode == "ssl" or (config.tls_mode == "auto" and config.smtp_port == 465):
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(config.smtp_server, config.smtp_port, context=ctx, timeout=20) as s:
                s.login(config.smtp_user, config.smtp_pass)
                s.sendmail(msg["From"], config.to, msg.as_string())
        else:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=20) as s:
                s.ehlo()
                s.starttls(context=ctx)
                s.ehlo()
                s.login(config.smtp_user, config.smtp_pass)
                s.sendmail(msg["From"], config.to, msg.as_string())
        return "sent"
    except Exception as e:
        logger.warning(f"Email send failed: {e}")
        return f"failed: {e}"
