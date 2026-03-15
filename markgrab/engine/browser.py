"""Browser engine — Playwright headless for JS-rendered and bot-protected pages."""

import logging

from markgrab.engine.base import Engine, FetchResult

logger = logging.getLogger(__name__)


class BrowserEngine(Engine):
    """Playwright-based browser engine for JS-heavy and bot-protected sites.

    Requires: pip install markgrab[browser]
    Playwright is imported lazily — the class can be imported without playwright installed.

    Args:
        proxy: Proxy URL.
        stealth: Apply anti-bot stealth scripts (default: False).
    """

    def __init__(self, *, proxy: str | None = None, stealth: bool = False):
        super().__init__(proxy=proxy)
        self.stealth = stealth

    async def fetch(self, url: str, *, timeout: float = 30.0) -> FetchResult:
        from playwright.async_api import async_playwright

        timeout_ms = int(timeout * 1000)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context_kwargs: dict = {
                    "viewport": {"width": 1920, "height": 1080},
                    "locale": "en-US",
                    "timezone_id": "America/New_York",
                }
                if self.proxy:
                    context_kwargs["proxy"] = {"server": self.proxy}

                context = await browser.new_context(**context_kwargs)
                if self.stealth:
                    from markgrab.anti_bot.stealth import apply_stealth

                    await apply_stealth(context)

                page = await context.new_page()
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=timeout_ms,
                )

                # Best-effort wait for JS rendering (max 5s or half timeout)
                networkidle_ms = min(5000, timeout_ms // 2)
                try:
                    await page.wait_for_load_state("networkidle", timeout=networkidle_ms)
                except Exception:
                    pass  # DOM content is enough

                html = await page.content()
                status = response.status if response else 200
                headers = response.headers if response else {}

                return FetchResult(
                    html=html,
                    status_code=status,
                    content_type=headers.get("content-type", "text/html"),
                    final_url=page.url,
                )
            finally:
                await browser.close()
