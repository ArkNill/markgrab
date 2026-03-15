"""Tests for CLI interface."""

import json
import sys
from unittest.mock import AsyncMock, patch

from markgrab.__main__ import main
from markgrab.result import ExtractResult

_MOCK_RESULT = ExtractResult(
    title="Test Page",
    text="This is test content from the CLI.",
    markdown="# Test Page\n\nThis is test content from the CLI.",
    word_count=7,
    language="en",
    content_type="article",
    source_url="https://example.com",
    metadata={"domain": "example.com"},
)


def _patch_extract():
    return patch("markgrab.__main__.extract", new_callable=AsyncMock, return_value=_MOCK_RESULT)


def test_markdown_output(capsys):
    with _patch_extract(), patch.object(sys, "argv", ["markgrab", "https://example.com"]):
        main()
    out = capsys.readouterr().out
    assert "# Test Page" in out
    assert "test content" in out


def test_text_output(capsys):
    with _patch_extract(), patch.object(sys, "argv", ["markgrab", "https://example.com", "-f", "text"]):
        main()
    out = capsys.readouterr().out
    assert "Title: Test Page" in out
    assert "This is test content" in out


def test_json_output(capsys):
    with _patch_extract(), patch.object(sys, "argv", ["markgrab", "https://example.com", "-f", "json"]):
        main()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["title"] == "Test Page"
    assert data["word_count"] == 7
    assert data["language"] == "en"


def test_browser_flag():
    mock_extract = AsyncMock(return_value=_MOCK_RESULT)
    with patch("markgrab.__main__.extract", mock_extract):
        with patch.object(sys, "argv", ["markgrab", "https://example.com", "--browser"]):
            main()
    mock_extract.assert_awaited_once()
    call_kwargs = mock_extract.call_args[1]
    assert call_kwargs["use_browser"] is True


def test_max_chars_option():
    mock_extract = AsyncMock(return_value=_MOCK_RESULT)
    with patch("markgrab.__main__.extract", mock_extract):
        with patch.object(sys, "argv", ["markgrab", "https://example.com", "--max-chars", "1000"]):
            main()
    assert mock_extract.call_args[1]["max_chars"] == 1000


def test_timeout_option():
    mock_extract = AsyncMock(return_value=_MOCK_RESULT)
    with patch("markgrab.__main__.extract", mock_extract):
        with patch.object(sys, "argv", ["markgrab", "https://example.com", "--timeout", "60"]):
            main()
    assert mock_extract.call_args[1]["timeout"] == 60.0


def test_proxy_option():
    mock_extract = AsyncMock(return_value=_MOCK_RESULT)
    with patch("markgrab.__main__.extract", mock_extract):
        with patch.object(sys, "argv", ["markgrab", "https://example.com", "--proxy", "http://proxy:8080"]):
            main()
    assert mock_extract.call_args[1]["proxy"] == "http://proxy:8080"


def test_error_exits(capsys):
    mock_extract = AsyncMock(side_effect=ValueError("Something failed"))
    with patch("markgrab.__main__.extract", mock_extract):
        with patch.object(sys, "argv", ["markgrab", "https://example.com"]):
            try:
                main()
            except SystemExit as e:
                assert e.code == 1
    err = capsys.readouterr().err
    assert "Something failed" in err
