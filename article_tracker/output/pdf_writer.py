from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from article_tracker.models.article import Article

logger = logging.getLogger(__name__)


def write_pdf(articles: List[Article], out_dir: str, prefix: str = "papers") -> str | None:
    try:
        from weasyprint import HTML
    except ImportError:
        logger.warning("WeasyPrint not installed, PDF output skipped")
        return None

    from article_tracker.output.md_writer import write_markdown

    md_path = write_markdown(articles, out_dir, prefix)
    try:
        import markdown as md_lib
        md_text = Path(md_path).read_text(encoding="utf-8")
        html_text = md_lib.markdown(md_text, extensions=["extra", "tables"])
    except ImportError:
        html_text = f"<pre>{Path(md_path).read_text(encoding='utf-8')}</pre>"

    d = Path(out_dir)
    ts = Path(md_path).stem.split("_")[-1] if "_" in Path(md_path).stem else ""
    pdf_path = d / f"{prefix}_{ts}.pdf"
    try:
        HTML(string=html_text).write_pdf(str(pdf_path))
        return str(pdf_path)
    except Exception as e:
        logger.warning(f"PDF generation failed: {e}")
        return None
