"""Tests for HttpEngine."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from markgrab.engine.http import HttpEngine


@pytest.fixture
def engine():
    return HttpEngine()


def _mock_response(text="<html><body>Test</body></html>", status=200, content_type="text/html", url="https://example.com"):
    resp = MagicMock()
    resp.text = text
    resp.status_code = status
    resp.headers = {"content-type": content_type}
    resp.url = url
    resp.raise_for_status = MagicMock()
    return resp


def _mock_client(response):
    client = AsyncMock()
    client.get = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.mark.asyncio
async def test_fetch_success(engine):
    response = _mock_response()
    client = _mock_client(response)

    with patch("markgrab.engine.http.httpx.AsyncClient", return_value=client):
        result = await engine.fetch("https://example.com")

    assert result.html == "<html><body>Test</body></html>"
    assert result.status_code == 200
    assert "text/html" in result.content_type
    assert result.final_url == "https://example.com"


@pytest.mark.asyncio
async def test_fetch_follows_redirects(engine):
    response = _mock_response(url="https://example.com/final")
    client = _mock_client(response)

    with patch("markgrab.engine.http.httpx.AsyncClient", return_value=client):
        result = await engine.fetch("https://example.com/redirect")

    assert result.final_url == "https://example.com/final"


@pytest.mark.asyncio
async def test_fetch_raises_on_http_error(engine):
    response = _mock_response(status=404)
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=response
    )
    client = _mock_client(response)

    with patch("markgrab.engine.http.httpx.AsyncClient", return_value=client):
        with pytest.raises(httpx.HTTPStatusError):
            await engine.fetch("https://example.com/404")


@pytest.mark.asyncio
async def test_fetch_sets_user_agent(engine):
    response = _mock_response()
    client = _mock_client(response)

    with patch("markgrab.engine.http.httpx.AsyncClient", return_value=client) as mock_cls:
        await engine.fetch("https://example.com")

    call_kwargs = mock_cls.call_args[1]
    ua = call_kwargs["headers"]["User-Agent"]
    assert "Mozilla" in ua
