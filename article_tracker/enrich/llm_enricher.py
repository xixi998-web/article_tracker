from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from article_tracker.config.config_schema import LLMConfig
from article_tracker.models.article import Article

logger = logging.getLogger(__name__)


def _normalize_endpoint(base_url: str) -> str:
    if not base_url:
        raise ValueError("llm.base_url is empty")
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def _json_loose(s: str) -> Dict[str, Any]:
    m = re.search(r"\{[\s\S]*\}", s)
    if not m:
        return {}
    raw = m.group(0)
    try:
        return json.loads(raw)
    except Exception:
        t = re.sub(r",\s*([}\]])", r"\1", raw)
        try:
            return json.loads(t)
        except Exception:
            return {}


def _chat_request(
    base_url: str, api_key: str, model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.2, max_tokens: int = 600, timeout: int = 60,
) -> str:
    from article_tracker.infra import http_client
    url = _normalize_endpoint(base_url)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
    resp = http_client.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return data.get("choices", [{}])[0].get("text", "")


class LLMEnricher:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key or os.getenv(config.api_key_env, "")

    def enrich(self, articles: List[Article]) -> dict:
        stats = {"success": 0, "failed": 0, "skipped": 0}
        if not self.config.enabled or not self.api_key:
            stats["skipped"] = len(articles)
            return stats
        for article in articles:
            try:
                result = self._generate_bilingual(article)
                if result:
                    article.digest_en = result.get("digest_en", "")
                    article.digest_zh = result.get("digest_zh", "")
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.warning(f"LLM failed for '{article.title[:50]}': {e}")
                stats["failed"] += 1
        return stats

    def _generate_bilingual(self, article: Article) -> Optional[Dict[str, str]]:
        sys_prompt = self.config.system_prompt_en or "You are a precise academic assistant. Summarize papers concisely."
        user_payload = {
            "title": article.title,
            "abstract": article.abstract,
            "venue_or_comments": article.venue or article.comments or "",
        }
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content":
                "Given the paper metadata below, write TWO concise one-paragraph digests:\n"
                "1) English paragraph first.\n"
                "2) Then a Simplified Chinese paragraph.\n"
                "- Each paragraph must briefly cover: motivation, method, and main experimental results.\n"
                "- Do not include links, bullet lists, markdown, or headings. Plain sentences only.\n"
                '- Return STRICT JSON: {"digest_en": "...", "digest_zh": "..."}\n\n'
                f"DATA:\n{json.dumps(user_payload, ensure_ascii=False)}"
            },
        ]
        text = _chat_request(
            self.config.base_url, self.api_key, self.config.model,
            messages, temperature=0.2, max_tokens=600, timeout=self.config.timeout,
        )
        data = _json_loose(text)
        en = (data.get("digest_en") or "").strip()
        zh = (data.get("digest_zh") or "").strip()
        if en or zh:
            return {"digest_en": en, "digest_zh": zh}
        return None

    def translate(self, article: Article) -> None:
        if not self.api_key:
            return
        sys_prompt = "You are a precise academic translator. Translate to Simplified Chinese concisely and faithfully; keep technical terms."
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content":
                f'Translate the following to Simplified Chinese. Return ONLY JSON: {{"title_zh":"...","abstract_zh":"..."}}\n\n'
                f'DATA: {json.dumps({"title": article.title, "abstract": article.abstract}, ensure_ascii=False)}'
            },
        ]
        try:
            text = _chat_request(
                self.config.base_url, self.api_key, self.config.model,
                messages, temperature=0.0, max_tokens=600, timeout=self.config.timeout,
            )
            data = _json_loose(text)
            if data.get("title_zh"):
                article.title_zh = data["title_zh"].strip()
            if data.get("abstract_zh"):
                article.abstract_zh = data["abstract_zh"].strip()
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
