"""Tests for BrowserEngine (mocked Playwright)."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from markgrab.engine.browser import BrowserEngine


def _mock_playwright_chain(html="<html><body>Rendered</body></html>", status=200, url="https://example.com"):
    """Build a full mock of the Playwright async chain."""
    response = MagicMock()
    response.status = status
    response.headers = {"content-type": "text/html"}

    page = AsyncMock()
    page.content = AsyncMock(return_value=html)
    page.url = url
    page.goto = AsyncMock(return_value=response)
    page.wait_for_load_state = AsyncMock()

    context = AsyncMock()
    context.new_page = AsyncMock(return_value=page)
    context.add_init_script = AsyncMock()

    browser = AsyncMock()
    browser.new_context = AsyncMock(return_value=context)
    browser.close = AsyncMock()

    pw = AsyncMock()
    pw.chromium.launch = AsyncMock(return_value=browser)

    # async_playwright() returns async context manager
    pw_factory = MagicMock()
    pw_cm = AsyncMock()
    pw_cm.__aenter__ = AsyncMock(return_value=pw)
    pw_cm.__aexit__ = AsyncMock(return_value=False)
    pw_factory.return_value = pw_cm

    return pw_factory, browser, context, page


def _patch_playwright(pw_factory):
    """Patch playwright in sys.modules so local import finds it."""
    mock_api = MagicMock()
    mock_api.async_playwright = pw_factory
    return patch.dict(sys.modules, {
        "playwright": MagicMock(),
        "playwright.async_api": mock_api,
    })


@pytest.fixture
def engine():
    return BrowserEngine()


@pytest.mark.asyncio
async def test_fetch_success(engine):
    pw_factory, browser, context, page = _mock_playwright_chain(
        html="<html><body><h1>Hello</h1></body></html>",
        url="https://example.com/page",
    )

    with _patch_playwright(pw_factory):
        result = await engine.fetch("https://example.com/page")

    assert "<h1>Hello</h1>" in result.html
    assert result.status_code == 200
    assert result.final_url == "https://example.com/page"
    assert "text/html" in result.content_type


@pytest.mark.asyncio
async def test_stealth_not_applied_by_default(engine):
    pw_factory, browser, context, page = _mock_playwright_chain()

    with _patch_playwright(pw_factory):
        await engine.fetch("https://example.com")

    context.add_init_script.assert_not_called()


@pytest.mark.asyncio
async def test_stealth_applied_when_enabled():
    stealth_engine = BrowserEngine(stealth=True)
    pw_factory, browser, context, page = _mock_playwright_chain()

    with _patch_playwright(pw_factory):
        await stealth_engine.fetch("https://example.com")

    context.add_init_script.assert_called_once()
    script = context.add_init_script.call_args[0][0]
    assert "webdriver" in script


@pytest.mark.asyncio
async def test_browser_closed_on_success(engine):
    pw_factory, browser, context, page = _mock_playwright_chain()

    with _patch_playwright(pw_factory):
        await engine.fetch("https://example.com")

    browser.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_browser_closed_on_error(engine):
    pw_factory, browser, context, page = _mock_playwright_chain()
    page.goto.side_effect = TimeoutError("Navigation timeout")

    with _patch_playwright(pw_factory):
        with pytest.raises(TimeoutError):
            await engine.fetch("https://example.com")

    browser.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_networkidle_timeout_ignored(engine):
    pw_factory, browser, context, page = _mock_playwright_chain()
    page.wait_for_load_state.side_effect = TimeoutError("networkidle timeout")

    with _patch_playwright(pw_factory):
        result = await engine.fetch("https://example.com")

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_none_response_handled(engine):
    pw_factory, browser, context, page = _mock_playwright_chain()
    page.goto = AsyncMock(return_value=None)

    with _patch_playwright(pw_factory):
        result = await engine.fetch("https://example.com")

    assert result.status_code == 200
    assert result.content_type == "text/html"


@pytest.mark.asyncio
async def test_redirect_captured(engine):
    pw_factory, browser, context, page = _mock_playwright_chain(url="https://example.com/final")

    with _patch_playwright(pw_factory):
        result = await engine.fetch("https://example.com/redirect")

    assert result.final_url == "https://example.com/final"
