"""HTTP engine — lightweight fetching with httpx."""

import logging
import random

import httpx

from markgrab.engine.base import USER_AGENTS, Engine, FetchResult

logger = logging.getLogger(__name__)


class HttpEngine(Engine):
    """Lightweight HTTP engine using httpx."""

    async def fetch(self, url: str, *, timeout: float = 30.0) -> FetchResult:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
        }

        async with httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            timeout=httpx.Timeout(timeout),
            proxy=self.proxy,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

            return FetchResult(
                html=response.text,
                status_code=response.status_code,
                content_type=response.headers.get("content-type", ""),
                final_url=str(response.url),
            )
