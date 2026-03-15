"""Tests for ExtractResult dataclass."""

from markgrab.result import ExtractResult


def test_create_result():
    result = ExtractResult(
        title="Test",
        text="Hello world",
        markdown="# Hello world",
        word_count=2,
        language="en",
        content_type="article",
        source_url="https://example.com",
    )
    assert result.title == "Test"
    assert result.text == "Hello world"
    assert result.markdown == "# Hello world"
    assert result.word_count == 2
    assert result.language == "en"
    assert result.content_type == "article"
    assert result.source_url == "https://example.com"
    assert result.metadata == {}


def test_result_with_metadata():
    result = ExtractResult(
        title="Test",
        text="text",
        markdown="md",
        word_count=1,
        language="en",
        content_type="article",
        source_url="https://example.com",
        metadata={"author": "Author", "domain": "example.com"},
    )
    assert result.metadata["author"] == "Author"
    assert result.metadata["domain"] == "example.com"
