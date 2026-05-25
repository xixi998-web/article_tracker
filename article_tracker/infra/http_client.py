from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

DEFAULT_TIMEOUT = float(os.getenv("AT_HTTP_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("AT_HTTP_MAX_RETRIES", "3"))
BASE_DELAY = float(os.getenv("AT_HTTP_BASE_DELAY", "1.0"))
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

_client: Optional[httpx.Client] = None


def get_client() -> httpx.Client:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT, connect=10.0),
            follow_redirects=True,
            headers={"User-Agent": "article-tracker/0.1"},
        )
    return _client


def close_client() -> None:
    global _client
    if _client and not _client.is_closed:
        _client.close()
    _client = None


def request_with_retry(
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
) -> httpx.Response:
    import random
    import time

    client = get_client()
    last_err: Optional[Exception] = None
    effective_timeout = timeout or DEFAULT_TIMEOUT

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.request(
                method, url, params=params, headers=headers,
                json=json, timeout=effective_timeout,
            )
            if resp.status_code in RETRYABLE_STATUS:
                raise httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}", request=resp.request, response=resp
                )
            return resp
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
            last_err = e
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code not in RETRYABLE_STATUS:
                raise
            if attempt < MAX_RETRIES:
                delay = min(BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.5), 20.0)
                time.sleep(delay)

    if last_err:
        raise last_err
    raise RuntimeError("Unknown HTTP request error")


def get(url: str, **kwargs) -> httpx.Response:
    return request_with_retry("GET", url, **kwargs)


def post(url: str, **kwargs) -> httpx.Response:
    return request_with_retry("POST", url, **kwargs)
