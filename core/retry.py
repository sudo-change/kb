"""Simple retry helper with exponential backoff for HTTP requests."""

from __future__ import annotations

import logging
import time
from typing import TypeVar, Callable

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 1.0  # seconds


def http_get_with_retry(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 30,
    max_retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
) -> httpx.Response:
    """GET request with retry logic and exponential backoff.

    Retries on 429, 5xx, and connection errors.
    Raises the last exception if all retries fail.
    """
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            resp = httpx.get(url, params=params, headers=headers, timeout=timeout)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", backoff * (2 ** attempt)))
                logger.warning(f"Rate limited on {url}, waiting {retry_after}s")
                time.sleep(retry_after)
                continue

            if resp.status_code >= 500:
                logger.warning(f"Server error {resp.status_code} on {url}, attempt {attempt + 1}/{max_retries}")
                time.sleep(backoff * (2 ** attempt))
                continue

            resp.raise_for_status()
            return resp

        except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadTimeout) as e:
            last_error = e
            logger.warning(f"Connection error on {url}: {e}, attempt {attempt + 1}/{max_retries}")
            time.sleep(backoff * (2 ** attempt))
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 500, 502, 503, 504):
                last_error = e
                time.sleep(backoff * (2 ** attempt))
                continue
            raise

    raise last_error or httpx.ConnectError(f"All {max_retries} retries failed for {url}")
