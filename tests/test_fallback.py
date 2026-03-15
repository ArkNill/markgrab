"""Tests for auto-fallback logic in extract()."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from markgrab import extract
from markgrab.engine.base import FetchResult


def _mock_http_engine(html="<html><body>OK</body></html>", url="https://example.com"):
    engine = AsyncMock()
    engine.fetch = AsyncMock(return_value=FetchResult(
        html=html, status_code=200, content_type="text/html", final_url=url,
    ))
    return engine


def _mock_http_engine_error(exc):
    engine = AsyncMock()
    engine.fetch = AsyncMock(side_effect=exc)
    return engine


def _make_fetch_result(html, url="https://example.com"):
    return FetchResult(html=html, status_code=200, content_type="text/html", final_url=url)


RICH_HTML = """\
<html><body><article>
<h1>Title</h1>
<p>This article has enough content to pass the minimum word count threshold
for the SPA detection logic in the extract function. We need at least fifty
words in total for this test to work properly and verify that the fallback
mechanism does not trigger when content is sufficiently rich.</p>
<p>Additional paragraph with more meaningful text content here to ensure
we have well over fifty words in the extracted text output.</p>
</article></body></html>"""

THIN_HTML = "<html><body><div id='root'></div></body></html>"

RENDERED_HTML = """\
<html><body><article>
<h1>Rendered Title</h1>
<p>This content was rendered by JavaScript and now has plenty of meaningful
text for the parser to extract and process correctly.</p>
</article></body></html>"""


def _mock_browser_engine(html=RICH_HTML, url="https://example.com"):
    """Create a mock BrowserEngine class (sync constructor, async fetch)."""
    mock_instance = MagicMock()
    mock_instance.fetch = AsyncMock(return_value=_make_fetch_result(html, url))
    mock_cls = MagicMock(return_value=mock_instance)
    return mock_cls


# --- HTTP error → browser fallback ---


@pytest.mark.asyncio
async def test_http_error_triggers_browser_fallback():
    with (
        patch("markgrab.core._BROWSER_AVAILABLE", True),
        patch("markgrab.core.BrowserEngine", _mock_browser_engine()),
        patch("markgrab.core.HttpEngine", return_value=_mock_http_engine_error(
            httpx.ConnectError("Connection refused")
        )),
    ):
        result = await extract("https://example.com")

    assert result.word_count > 0
    assert "enough content" in result.text


@pytest.mark.asyncio
async def test_http_error_no_browser_raises():
    with (
        patch("markgrab.core._BROWSER_AVAILABLE", False),
        patch("markgrab.core.HttpEngine", return_value=_mock_http_engine_error(
            httpx.ConnectError("Connection refused")
        )),
    ):
        with pytest.raises(httpx.ConnectError):
            await extract("https://example.com")


# --- Thin content → browser retry ---


@pytest.mark.asyncio
async def test_thin_content_retries_with_browser():
    mock_browser = _mock_browser_engine(html=RENDERED_HTML)
    http_engine = _mock_http_engine(html=THIN_HTML)

    with (
        patch("markgrab.core._BROWSER_AVAILABLE", True),
        patch("markgrab.core.BrowserEngine", mock_browser),
    ):
        result = await extract("https://example.com", engine=http_engine)

    assert "rendered by JavaScript" in result.text
    mock_browser.return_value.fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_thin_content_no_browser_keeps_original():
    http_engine = _mock_http_engine(html=THIN_HTML)

    with patch("markgrab.core._BROWSER_AVAILABLE", False):
        result = await extract("https://example.com", engine=http_engine)

    assert result.word_count < 50


@pytest.mark.asyncio
async def test_thin_content_browser_fails_keeps_original():
    mock_instance = MagicMock()
    mock_instance.fetch = AsyncMock(side_effect=TimeoutError("Browser timeout"))
    mock_browser = MagicMock(return_value=mock_instance)

    http_engine = _mock_http_engine(html=THIN_HTML)

    with (
        patch("markgrab.core._BROWSER_AVAILABLE", True),
        patch("markgrab.core.BrowserEngine", mock_browser),
    ):
        result = await extract("https://example.com", engine=http_engine)

    assert result.word_count < 50


# --- Rich content → no fallback ---


@pytest.mark.asyncio
async def test_rich_content_no_browser_retry():
    mock_browser = _mock_browser_engine()
    http_engine = _mock_http_engine(html=RICH_HTML)

    with (
        patch("markgrab.core._BROWSER_AVAILABLE", True),
        patch("markgrab.core.BrowserEngine", mock_browser),
    ):
        result = await extract("https://example.com", engine=http_engine)

    assert result.word_count >= 50
    mock_browser.return_value.fetch.assert_not_awaited()


# --- use_browser=True ---


@pytest.mark.asyncio
async def test_use_browser_forces_browser():
    mock_browser = _mock_browser_engine()

    with (
        patch("markgrab.core._BROWSER_AVAILABLE", True),
        patch("markgrab.core.BrowserEngine", mock_browser),
    ):
        result = await extract("https://example.com", use_browser=True)

    mock_browser.return_value.fetch.assert_awaited_once()
    assert result.word_count > 0


@pytest.mark.asyncio
async def test_use_browser_no_playwright_raises():
    with patch("markgrab.core._BROWSER_AVAILABLE", False):
        with pytest.raises(ImportError, match="Playwright"):
            await extract("https://example.com", use_browser=True)
