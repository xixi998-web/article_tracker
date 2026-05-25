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


def _esc(x: Optional[str]) -> str:
    return html_mod.escape(x or "", quote=True)


def _render_card(a: Article) -> str:
    parts = ['<div style="border:1px solid #e5e7eb;border-radius:14px;padding:14px;margin:12px 0;">']
    parts.append(f'<div style="font-weight:700;font-size:16px;margin:0 0 6px 0;">{_esc(a.title)}</div>')
    if a.authors:
        parts.append(f'<div style="color:#667085;font-size:13px;">Authors: {_esc(", ".join(a.authors[:5]))}</div>')
    if a.venue:
        parts.append(f'<div style="color:#667085;font-size:13px;">Venue: {_esc(a.venue)}</div>')
    if a.published:
        parts.append(f'<div style="color:#667085;font-size:13px;">Published: {_esc(a.published)}</div>')
    tier = a.screening_tier.value if a.screening_tier else ""
    if tier:
        parts.append(f'<div style="color:#667085;font-size:13px;">Tier: {tier}</div>')
    links = []
    if a.html_url:
        links.append(f'<a href="{_esc(a.html_url)}">Abs</a>')
    if a.pdf_url:
        links.append(f'<a href="{_esc(a.pdf_url)}">PDF</a>')
    for i, u in enumerate(a.code_links[:3]):
        links.append(f'<a href="{_esc(u)}">Code{i+1}</a>')
    if links:
        parts.append(f'<div style="margin:8px 0">{" · ".join(links)}</div>')
    if a.abstract:
        parts.append(f'<details><summary>Abstract</summary><div style="white-space:pre-wrap">{_esc(a.abstract)}</div></details>')
    if a.digest_en:
        parts.append(f'<div style="margin-top:8px;white-space:pre-wrap"><b>Summary:</b> {_esc(a.digest_en)}</div>')
    if a.digest_zh:
        parts.append(f'<div style="margin-top:8px;white-space:pre-wrap"><b>总结：</b>{_esc(a.digest_zh)}</div>')
    parts.append('</div>')
    return "\n".join(parts)


def send_email(articles: List[Article], config: EmailConfig, subject_prefix: str = "Paper Tracker") -> str | None:
    if not config.enabled:
        return None
    html_body = f"""<meta charset="utf-8"><div style="font-family:ui-sans-serif,system-ui;max-width:900px;margin:0 auto;padding:18px;">
<h2>{_esc(subject_prefix)} — {datetime.now().strftime("%Y-%m-%d")}</h2>"""
    for a in articles[:50]:
        html_body += _render_card(a)
    html_body += "</div>"

    msg = MIMEMultipart()
    msg["From"] = config.sender
    msg["To"] = ", ".join(config.to)
    msg["Subject"] = f"{subject_prefix} — {datetime.now().strftime('%Y-%m-%d')}"
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
