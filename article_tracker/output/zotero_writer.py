from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List
from xml.etree.ElementTree import Element, SubElement, indent, tostring

from article_tracker.models.article import Article


def write_zotero(articles: List[Article], out_dir: str, prefix: str = "papers") -> str:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = d / f"{prefix}_{ts}.rdf"

    rdf = Element("RDF", xmlns="http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    for a in articles:
        item = SubElement(rdf, "Description")
        SubElement(item, "type").text = "journalArticle"
        SubElement(item, "title").text = a.title
        if a.authors:
            SubElement(item, "creators").text = "; ".join(a.authors)
        if a.abstract:
            SubElement(item, "abstractNote").text = a.abstract
        if a.venue:
            SubElement(item, "publicationTitle").text = a.venue
        if a.published:
            SubElement(item, "date").text = a.published
        if a.doi:
            SubElement(item, "DOI").text = a.doi
        tier = a.screening_tier.value if a.screening_tier else ""
        if tier:
            SubElement(item, "tags").text = tier
        if a.html_url:
            SubElement(item, "url").text = a.html_url

    indent(rdf)
    xml_bytes = tostring(rdf, encoding="unicode", xml_declaration=True)
    path.write_text(xml_bytes, encoding="utf-8")
    return str(path)
