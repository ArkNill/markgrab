"""Tests for extract_batch() — concurrent URL extraction without threads."""

import asyncio
import time
from unittest.mock import patch

import pytest

from markgrab import extract_batch
from markgrab.result import ExtractResult


def _ok_result(url="https://example.com", word_count=100):
    return ExtractResult(
        title="Test",
        text="test " * word_count,
        markdown="test " * word_count,
        word_count=word_count,
        language="en",
        content_type="html",
        source_url=url,
    )


# --- Basic functionality ---


@pytest.mark.asyncio
async def test_batch_returns_all_results():
    urls = ["https://a.com", "https://b.com", "https://c.com"]

    async def _fake_extract(url, **kwargs):
        return _ok_result(url=url)

    with patch("markgrab.core.extract", side_effect=_fake_extract):
        results = await extract_batch(urls, domain_delay=0)

    assert len(results) == 3
    assert all(isinstance(r, ExtractResult) for r in results)
    assert [r.source_url for r in results] == urls


@pytest.mark.asyncio
async def test_batch_partial_failure():
    urls = ["https://ok.com", "https://fail.com", "https://ok2.com"]

    async def _fake_extract(url, **kwargs):
        if "fail" in url:
            raise ConnectionError("refused")
        return _ok_result(url=url)

    with patch("markgrab.core.extract", side_effect=_fake_extract):
        results = await extract_batch(urls, domain_delay=0)

    assert len(results) == 3
    assert isinstance(results[0], ExtractResult)
    assert isinstance(results[1], ConnectionError)
    assert isinstance(results[2], ExtractResult)


@pytest.mark.asyncio
async def test_batch_empty_urls():
    results = await extract_batch([])
    assert results == []


# --- Concurrency control ---


@pytest.mark.asyncio
async def test_batch_concurrency_limit():
    """Verify max_concurrent limits simultaneous extractions."""
    active = 0
    max_active = 0

    async def _fake_extract(url, **kwargs):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.05)
        active -= 1
        return _ok_result(url=url)

    urls = [f"https://site{i}.com" for i in range(6)]
    with patch("markgrab.core.extract", side_effect=_fake_extract):
        results = await extract_batch(urls, max_concurrent=2, domain_delay=0)

    assert len(results) == 6
    assert all(isinstance(r, ExtractResult) for r in results)
    assert max_active <= 2


# --- Timeouts ---


@pytest.mark.asyncio
async def test_batch_per_url_timeout():
    async def _slow_extract(url, **kwargs):
        if "slow" in url:
            await asyncio.sleep(10)
        return _ok_result(url=url)

    urls = ["https://fast.com", "https://slow.com"]
    with patch("markgrab.core.extract", side_effect=_slow_extract):
        results = await extract_batch(urls, per_url_timeout=0.1, domain_delay=0)

    assert isinstance(results[0], ExtractResult)
    assert isinstance(results[1], (asyncio.TimeoutError, TimeoutError))


# --- Domain delay ---


@pytest.mark.asyncio
async def test_batch_domain_delay():
    """Same-domain URLs should be spaced by domain_delay."""
    timestamps = []

    async def _fake_extract(url, **kwargs):
        timestamps.append(time.monotonic())
        return _ok_result(url=url)

    urls = ["https://same.com/a", "https://same.com/b", "https://same.com/c"]
    with patch("markgrab.core.extract", side_effect=_fake_extract):
        await extract_batch(urls, max_concurrent=6, domain_delay=0.2)

    assert len(timestamps) == 3
    # Each request to same domain should be ~0.2s apart
    for i in range(1, len(timestamps)):
        gap = timestamps[i] - timestamps[i - 1]
        assert gap >= 0.15, f"Gap {gap:.3f}s < 0.15s between same-domain requests"


# --- Browser fallback parameter passthrough ---


@pytest.mark.asyncio
async def test_batch_with_browser_fallback():
    """Verify browser_fallback parameter is passed through to extract()."""
    captured_kwargs = []

    async def _fake_extract(url, **kwargs):
        captured_kwargs.append(kwargs)
        return _ok_result(url=url)

    with patch("markgrab.core.extract", side_effect=_fake_extract):
        await extract_batch(
            ["https://example.com"],
            browser_fallback=True,
            timeout=15.0,
            max_chars=20_000,
            domain_delay=0,
        )

    assert len(captured_kwargs) == 1
    assert captured_kwargs[0]["browser_fallback"] is True
    assert captured_kwargs[0]["timeout"] == 15.0
    assert captured_kwargs[0]["max_chars"] == 20_000


# --- Duplicate URLs ---


@pytest.mark.asyncio
async def test_batch_duplicate_urls():
    """Duplicate URLs are extracted independently (no dedup)."""
    call_count = 0

    async def _fake_extract(url, **kwargs):
        nonlocal call_count
        call_count += 1
        return _ok_result(url=url)

    urls = ["https://same.com", "https://same.com"]
    with patch("markgrab.core.extract", side_effect=_fake_extract):
        results = await extract_batch(urls, domain_delay=0)

    assert len(results) == 2
    assert call_count == 2


# --- Semaphore not held during domain delay ---


@pytest.mark.asyncio
async def test_batch_domain_delay_does_not_block_other_domains():
    """Domain delay for one domain must not block different domains."""
    order = []

    async def _fake_extract(url, **kwargs):
        order.append(url)
        return _ok_result(url=url)

    # slow.com has 3 URLs → domain delay serializes them
    # fast.com has 1 URL → should not wait for slow.com's delays
    urls = [
        "https://slow.com/1",
        "https://slow.com/2",
        "https://slow.com/3",
        "https://fast.com/1",
    ]
    with patch("markgrab.core.extract", side_effect=_fake_extract):
        results = await extract_batch(urls, max_concurrent=4, domain_delay=0.3)

    assert len(results) == 4
    assert all(isinstance(r, ExtractResult) for r in results)
    # fast.com should not wait for slow.com's ~0.6s total delay
    # Total time should be ~0.6s (slow.com serialized), not ~0.9s
    assert "https://fast.com/1" in order[:2], (
        f"fast.com should start early, not blocked by slow.com delays. Order: {order}"
    )


# --- Overall batch timeout (Forge pattern) ---


@pytest.mark.asyncio
async def test_batch_overall_timeout():
    """Wrapping extract_batch in wait_for works (Forge pattern)."""

    async def _slow_extract(url, **kwargs):
        await asyncio.sleep(10)
        return _ok_result(url=url)

    urls = ["https://a.com", "https://b.com"]
    with patch("markgrab.core.extract", side_effect=_slow_extract):
        with pytest.raises((asyncio.TimeoutError, TimeoutError)):
            await asyncio.wait_for(
                extract_batch(urls, domain_delay=0),
                timeout=0.2,
            )
