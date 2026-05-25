from __future__ import annotations

import logging
from typing import List

from article_tracker.config.config_schema import UnifiedConfig
from article_tracker.models.article import Article

from .email_sender import send_email
from .excel_writer import write_excel
from .ghpages_publisher import publish_ghpages
from .html_table_writer import write_html_table
from .json_writer import write_json
from .md_writer import write_markdown
from .obsidian_writer import write_obsidian
from .pdf_writer import write_pdf
from .zotero_writer import write_zotero

logger = logging.getLogger(__name__)


class OutputManager:
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.output_config = config.output

    def output(self, articles: List[Article]) -> dict:
        results = {}
        oc = self.output_config
        out_dir = oc.dir

        try:
            if oc.json_enabled:
                results["json"] = write_json(articles, out_dir)
        except Exception as e:
            logger.warning(f"JSON output failed: {e}")
            results["json"] = f"failed: {e}"

        try:
            if oc.md_enabled:
                results["markdown"] = write_markdown(articles, out_dir)
        except Exception as e:
            logger.warning(f"Markdown output failed: {e}")
            results["markdown"] = f"failed: {e}"

        try:
            if oc.pdf_enabled:
                results["pdf"] = write_pdf(articles, out_dir)
        except Exception as e:
            logger.warning(f"PDF output failed: {e}")
            results["pdf"] = f"failed: {e}"

        try:
            if oc.excel_enabled:
                results["excel"] = write_excel(articles, out_dir)
        except Exception as e:
            logger.warning(f"Excel output failed: {e}")
            results["excel"] = f"failed: {e}"

        try:
            if oc.html_table_enabled:
                results["html_table"] = write_html_table(articles, out_dir)
        except Exception as e:
            logger.warning(f"HTML table output failed: {e}")
            results["html_table"] = f"failed: {e}"

        try:
            if oc.obsidian_enabled and oc.obsidian_vault:
                count = write_obsidian(articles, oc.obsidian_vault)
                results["obsidian"] = f"{count} notes"
        except Exception as e:
            logger.warning(f"Obsidian output failed: {e}")
            results["obsidian"] = f"failed: {e}"

        try:
            if oc.zotero_enabled:
                results["zotero"] = write_zotero(articles, out_dir)
        except Exception as e:
            logger.warning(f"Zotero output failed: {e}")
            results["zotero"] = f"failed: {e}"

        try:
            if oc.email.enabled:
                result = send_email(articles, oc.email, oc.email.subject_prefix)
                results["email"] = result or "skipped"
        except Exception as e:
            logger.warning(f"Email output failed: {e}")
            results["email"] = f"failed: {e}"

        try:
            if oc.ghpages.enabled:
                results["ghpages"] = publish_ghpages(articles, oc.ghpages)
        except Exception as e:
            logger.warning(f"GitHub Pages output failed: {e}")
            results["ghpages"] = f"failed: {e}"

        return results
