"""Main orchestrator — route URL to appropriate engine and parser."""

import asyncio
import logging
import random
from urllib.parse import urlparse

import httpx

from markgrab.engine.base import USER_AGENTS, Engine
from markgrab.engine.browser import BrowserEngine
from markgrab.engine.http import HttpEngine
from markgrab.filter.truncate import truncate_result
from markgrab.parser.html import HtmlParser
from markgrab.parser.youtube import YouTubeParser, _extract_video_id
from markgrab.result import ExtractResult

logger = logging.getLogger(__name__)

# Minimum word count — below this, content is likely SPA/JS-only
_MIN_WORD_COUNT = 50

_OEMBED_URL = "https://www.youtube.com/oembed?url={url}&format=json"

try:
    import playwright  # noqa: F401

    _BROWSER_AVAILABLE = True
except ImportError:
    _BROWSER_AVAILABLE = False


def _detect_type_from_url(url: str) -> str:
    """Detect content type from URL pattern."""
    parsed = urlparse(url)
    path = parsed.path.lower()

    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        return "youtube"
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith(".docx"):
        return "docx"

    return "html"


async def _fetch_with_fallback(
    url: str,
    *,
    engine: Engine | None = None,
    timeout: float = 30.0,
    proxy: str | None = None,
    stealth: bool = False,
    locale: str | None = None,
):
    """Fetch via HTTP, fallback to browser on error."""
    http_engine = engine or HttpEngine(proxy=proxy)
    try:
        return await http_engine.fetch(url, timeout=timeout)
    except Exception as exc:
        if _BROWSER_AVAILABLE:
            logger.info("HTTP failed for %s (%s), falling back to browser", url, type(exc).__name__)
            return await BrowserEngine(proxy=proxy, stealth=stealth, locale=locale).fetch(url, timeout=timeout)
        raise


async def _fetch_youtube_title(url: str, timeout: float = 30.0) -> str:
    """Fetch YouTube video title via oEmbed API."""
    try:
        oembed_url = _OEMBED_URL.format(url=url)
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            resp = await client.get(oembed_url)
            if resp.status_code == 200:
                return resp.json().get("title", "")
    except Exception:
        logger.debug("Failed to fetch YouTube oEmbed title for %s", url)
    return ""


async def _fetch_bytes(url: str, *, timeout: float = 30.0, proxy: str | None = None) -> tuple[bytes, str]:
    """Fetch URL as raw bytes. Returns (data, final_url)."""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "*/*",
    }
    async with httpx.AsyncClient(
        headers=headers,
        follow_redirects=True,
        timeout=httpx.Timeout(timeout),
        proxy=proxy,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content, str(resp.url)


async def _extract_youtube(url: str, *, timeout: float = 30.0, max_chars: int = 50_000) -> ExtractResult:
    """Extract YouTube video transcript."""
    video_id = _extract_video_id(url)
    title = await _fetch_youtube_title(url, timeout=timeout)

    parser = YouTubeParser()
    result = parser.parse(video_id=video_id, url=url, title=title)
    return truncate_result(result, max_chars=max_chars)


async def _extract_binary(
    url: str,
    content_type: str,
    *,
    timeout: float = 30.0,
    max_chars: int = 50_000,
    proxy: str | None = None,
) -> ExtractResult:
    """Extract content from binary URLs (PDF, DOCX)."""
    data, final_url = await _fetch_bytes(url, timeout=timeout, proxy=proxy)

    if content_type == "pdf":
        from markgrab.parser.pdf import PdfParser

        result = PdfParser().parse(data, url=final_url)
    elif content_type == "docx":
        from markgrab.parser.docx import DocxParser

        result = DocxParser().parse(data, url=final_url)
    else:
        raise ValueError(f"Unknown binary content type: {content_type}")

    return truncate_result(result, max_chars=max_chars)


async def extract(
    url: str,
    *,
    engine: Engine | None = None,
    max_chars: int = 50_000,
    use_browser: bool = False,
    stealth: bool = False,
    timeout: float = 30.0,
    proxy: str | None = None,
    locale: str | None = None,
    browser_fallback: bool = True,
) -> ExtractResult:
    """Extract content from URL and return ExtractResult.

    Args:
        url: Target URL to extract content from.
        engine: Custom engine instance (default: HttpEngine, with browser fallback).
        max_chars: Maximum characters for text/markdown (default 50K).
        use_browser: Force Playwright browser rendering.
        stealth: Apply anti-bot stealth scripts when using browser (default: False).
        timeout: Request timeout in seconds.
        proxy: Proxy URL (e.g., "http://proxy:8080", "socks5://proxy:1080").
        locale: Browser locale (default: auto-detect from URL TLD, e.g. .kr → ko-KR).
        browser_fallback: Auto-fallback to browser on HTTP error or thin content (default: True).
            Set False for HTTP-only extraction (caller manages browser separately).
    """
    url_type = _detect_type_from_url(url)

    # YouTube — dedicated parser (no engine needed)
    if url_type == "youtube":
        return await _extract_youtube(url, timeout=timeout, max_chars=max_chars)

    # PDF / DOCX — binary fetch + dedicated parser
    if url_type in ("pdf", "docx"):
        return await _extract_binary(url, url_type, timeout=timeout, max_chars=max_chars, proxy=proxy)

    # HTML flow — engine + parser + fallback
    if use_browser:
        if not _BROWSER_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install 'markgrab[browser]'")
        fetch_result = await (engine or BrowserEngine(proxy=proxy, stealth=stealth, locale=locale)).fetch(
            url, timeout=timeout
        )
    else:
        if browser_fallback and _BROWSER_AVAILABLE:
            fetch_result = await _fetch_with_fallback(
                url, engine=engine, timeout=timeout, proxy=proxy, stealth=stealth, locale=locale
            )
        else:
            fetch_result = await (engine or HttpEngine(proxy=proxy)).fetch(url, timeout=timeout)

    # Content-Type header may reveal PDF even without .pdf extension
    if "application/pdf" in fetch_result.content_type:
        data, final_url = await _fetch_bytes(url, timeout=timeout, proxy=proxy)
        from markgrab.parser.pdf import PdfParser

        result = PdfParser().parse(data, url=final_url)
        return truncate_result(result, max_chars=max_chars)

    # Parse HTML
    parser = HtmlParser()
    result = parser.parse(fetch_result.html, url=fetch_result.final_url)

    # Auto-fallback: thin content likely means SPA/JS-only page
    if not use_browser and browser_fallback and _BROWSER_AVAILABLE and result.word_count < _MIN_WORD_COUNT:
        logger.info("Thin content (%d words) for %s, retrying with browser", result.word_count, url)
        try:
            browser_result = await BrowserEngine(proxy=proxy, stealth=stealth, locale=locale).fetch(
                url, timeout=timeout
            )
            browser_parsed = parser.parse(browser_result.html, url=browser_result.final_url)
            if browser_parsed.word_count > result.word_count:
                result = browser_parsed
        except Exception:
            pass  # Keep original result

    return truncate_result(result, max_chars=max_chars)


async def extract_batch(
    urls: list[str],
    *,
    max_concurrent: int = 6,
    domain_delay: float = 1.0,
    per_url_timeout: float | None = None,
    max_chars: int = 50_000,
    browser_fallback: bool = True,
    timeout: float = 30.0,
    proxy: str | None = None,
    stealth: bool = False,
    locale: str | None = None,
) -> list[ExtractResult | Exception]:
    """Extract content from multiple URLs concurrently.

    Uses asyncio concurrency (no threads) — browser fallback is safe.
    ThreadPoolExecutor causes Playwright deadlocks; this function avoids
    threads entirely by using asyncio.Semaphore + asyncio.gather.

    Args:
        urls: List of URLs to extract.
        max_concurrent: Maximum simultaneous extractions (default: 6).
        domain_delay: Minimum seconds between requests to the same domain (default: 1.0).
        per_url_timeout: Hard timeout per URL in seconds (None = no extra limit).
        max_chars: Maximum characters per result.
        browser_fallback: Auto-fallback to browser on HTTP error or thin content.
        timeout: Per-request soft timeout passed to extract().
        proxy: Proxy URL.
        stealth: Apply anti-bot stealth scripts.
        locale: Browser locale override.

    Returns:
        List parallel to *urls*: each element is an ExtractResult on success
        or an Exception on failure.
    """
    if not urls:
        return []

    sem = asyncio.Semaphore(max_concurrent)

    # Per-domain locks for rate limiting
    domains = {urlparse(u).hostname or "" for u in urls}
    domain_locks: dict[str, asyncio.Lock] = {d: asyncio.Lock() for d in domains}
    domain_last: dict[str, float] = {}

    async def _wait_domain(url: str) -> None:
        if domain_delay <= 0:
            return
        domain = urlparse(url).hostname or ""
        lock = domain_locks.get(domain)
        if lock is None:
            return
        async with lock:
            import time as _time

            last = domain_last.get(domain, 0.0)
            now = _time.monotonic()
            wait = domain_delay - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            domain_last[domain] = _time.monotonic()

    async def _extract_one(url: str) -> ExtractResult:
        await _wait_domain(url)
        async with sem:
            coro = extract(
                url,
                max_chars=max_chars,
                browser_fallback=browser_fallback,
                timeout=timeout,
                proxy=proxy,
                stealth=stealth,
                locale=locale,
            )
            if per_url_timeout is not None:
                return await asyncio.wait_for(coro, timeout=per_url_timeout)
            return await coro

    return await asyncio.gather(
        *[_extract_one(url) for url in urls],
        return_exceptions=True,
    )
