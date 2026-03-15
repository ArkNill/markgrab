"""Tests for truncate filter."""

from markgrab.filter.truncate import truncate_result
from markgrab.result import ExtractResult


def _make_result(text: str = "short", markdown: str = "short") -> ExtractResult:
    return ExtractResult(
        title="Test",
        text=text,
        markdown=markdown,
        word_count=len(text.split()),
        language="en",
        content_type="article",
        source_url="https://example.com",
    )


def test_no_truncation_needed():
    result = _make_result()
    truncated = truncate_result(result, max_chars=1000)
    assert truncated is result  # Same object returned


def test_text_truncated():
    long_text = "word " * 20000  # ~100K chars
    result = _make_result(text=long_text, markdown=long_text)
    truncated = truncate_result(result, max_chars=100)
    assert len(truncated.text) < 200
    assert "[truncated]" in truncated.text


def test_markdown_truncated():
    long_md = "# heading\n\n" + "paragraph " * 20000
    result = _make_result(markdown=long_md)
    truncated = truncate_result(result, max_chars=100)
    assert "[truncated]" in truncated.markdown


def test_word_count_updated():
    long_text = "word " * 20000
    result = _make_result(text=long_text)
    truncated = truncate_result(result, max_chars=100)
    assert truncated.word_count < result.word_count


def test_zero_max_chars_no_truncation():
    result = _make_result()
    truncated = truncate_result(result, max_chars=0)
    assert truncated is result


def test_truncation_at_newline():
    text = "line one\nline two\nline three\nline four"
    result = _make_result(text=text, markdown=text)
    truncated = truncate_result(result, max_chars=20)
    assert "[truncated]" in truncated.text


def test_metadata_preserved():
    result = _make_result(text="word " * 20000)
    result = ExtractResult(
        title="Keep",
        text="word " * 20000,
        markdown="md",
        word_count=20000,
        language="ko",
        content_type="article",
        source_url="https://example.com/page",
        metadata={"author": "Me"},
    )
    truncated = truncate_result(result, max_chars=100)
    assert truncated.title == "Keep"
    assert truncated.language == "ko"
    assert truncated.source_url == "https://example.com/page"
    assert truncated.metadata["author"] == "Me"
