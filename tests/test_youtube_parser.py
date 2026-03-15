"""Tests for YouTubeParser."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from markgrab.parser.youtube import YouTubeParser, _extract_video_id

# --- Video ID extraction ---


def test_extract_video_id_watch_url():
    assert _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_short_url():
    assert _extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_with_params():
    assert _extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ&t=120") == "dQw4w9WgXcQ"


def test_extract_video_id_invalid():
    with pytest.raises(ValueError, match="Cannot extract video ID"):
        _extract_video_id("https://example.com/page")


def test_extract_video_id_missing_v():
    with pytest.raises(ValueError, match="Cannot extract video ID"):
        _extract_video_id("https://youtube.com/watch?list=abc")


# --- YouTubeParser.parse ---


def _mock_transcript_api(snippets):
    """Create mock YouTubeTranscriptApi and patch sys.modules."""
    mock_snippet_list = []
    for s in snippets:
        snippet = MagicMock()
        snippet.text = s["text"]
        snippet.start = s["start"]
        snippet.duration = s["duration"]
        mock_snippet_list.append(snippet)

    mock_fetched = MagicMock()
    mock_fetched.__iter__ = MagicMock(return_value=iter(mock_snippet_list))

    mock_transcript = MagicMock()
    mock_transcript.fetch = MagicMock(return_value=mock_fetched)
    mock_transcript.language_code = "en"

    mock_transcript_list = MagicMock()
    mock_transcript_list.find_transcript = MagicMock(return_value=mock_transcript)
    mock_transcript_list.__iter__ = MagicMock(return_value=iter([mock_transcript]))

    mock_api_instance = MagicMock()
    mock_api_instance.list = MagicMock(return_value=mock_transcript_list)

    mock_api_cls = MagicMock(return_value=mock_api_instance)

    mock_module = MagicMock()
    mock_module.YouTubeTranscriptApi = mock_api_cls

    return patch.dict(sys.modules, {"youtube_transcript_api": mock_module})


def test_parse_basic():
    snippets = [
        {"text": "Hello world this is a test video", "start": 0.0, "duration": 5.0},
        {"text": "with enough content to verify parsing", "start": 5.0, "duration": 5.0},
        {"text": "works correctly in our test suite", "start": 10.0, "duration": 5.0},
    ]

    with _mock_transcript_api(snippets):
        parser = YouTubeParser()
        result = parser.parse(video_id="dQw4w9WgXcQ", url="https://youtube.com/watch?v=dQw4w9WgXcQ", title="Test")

    assert result.title == "Test"
    assert result.content_type == "video"
    assert "Hello world" in result.text
    assert result.word_count > 0
    assert result.metadata["video_id"] == "dQw4w9WgXcQ"


def test_parse_timestamps_in_markdown():
    snippets = [
        {"text": "First line", "start": 65.0, "duration": 3.0},
        {"text": "Second line", "start": 130.0, "duration": 4.0},
    ]

    with _mock_transcript_api(snippets):
        parser = YouTubeParser()
        result = parser.parse(video_id="abc12345678", url="https://youtube.com/watch?v=abc12345678", title="Video")

    assert "[01:05]" in result.markdown
    assert "[02:10]" in result.markdown


def test_parse_no_title_uses_fallback():
    snippets = [{"text": "Some content here", "start": 0.0, "duration": 5.0}]

    with _mock_transcript_api(snippets):
        parser = YouTubeParser()
        result = parser.parse(video_id="abc12345678", url="https://youtube.com/watch?v=abc12345678")

    assert "abc12345678" in result.title


def test_parse_korean_content():
    snippets = [
        {
            "text": (
                "인공지능 기술이 빠르게 발전하고 있습니다 최근 대규모 언어 모델의 등장으로"
                " 자연어 처리 분야에서 큰 진전이 이루어졌습니다"
            ),
            "start": 0.0,
            "duration": 10.0,
        },
    ]

    with _mock_transcript_api(snippets):
        parser = YouTubeParser()
        result = parser.parse(video_id="abc12345678", url="https://youtube.com/watch?v=abc12345678", title="한국어")

    assert result.language == "ko"


def test_parse_source_url_preserved():
    snippets = [{"text": "Content", "start": 0.0, "duration": 5.0}]

    with _mock_transcript_api(snippets):
        parser = YouTubeParser()
        url = "https://youtube.com/watch?v=abc12345678"
        result = parser.parse(video_id="abc12345678", url=url, title="Test")

    assert result.source_url == url
