"""Tests for HtmlParser."""

import pytest

from markgrab.parser.html import HtmlParser
from tests.fixtures import (
    HIDDEN_ELEMENTS_HTML,
    KOREAN_HTML,
    MINIMAL_HTML,
    NO_ARTICLE_HTML,
    NOISY_HTML,
    SIMPLE_HTML,
)


@pytest.fixture
def parser():
    return HtmlParser()


# --- Title Extraction ---


class TestTitleExtraction:
    def test_title_from_title_tag(self, parser):
        result = parser.parse(SIMPLE_HTML, "https://example.com")
        assert result.title == "Simple Article"

    def test_title_from_og_title(self, parser):
        result = parser.parse(NOISY_HTML, "https://example.com")
        assert result.title == "OG Title Override"

    def test_title_from_h1_fallback(self, parser):
        html = (
            "<html><body><article><h1>Fallback Title</h1>"
            "<p>Content long enough to pass the threshold for content extraction.</p>"
            "</article></body></html>"
        )
        result = parser.parse(html, "https://example.com")
        assert result.title == "Fallback Title"

    def test_empty_title(self, parser):
        result = parser.parse("<html><body><p>No title here</p></body></html>", "https://example.com")
        assert result.title == ""


# --- Noise Removal ---


class TestNoiseRemoval:
    def test_script_removed(self, parser):
        result = parser.parse(NOISY_HTML, "https://example.com")
        assert "analytics" not in result.text
        assert "trackPageView" not in result.text

    def test_style_removed(self, parser):
        result = parser.parse(NOISY_HTML, "https://example.com")
        assert ".ad" not in result.text

    def test_cookie_banner_removed_body_fallback(self, parser):
        html = """\
<html><body>
<div class="cookie-banner">Accept our cookies please</div>
<h1>Main Page</h1>
<p>Content text with enough words to be properly extracted and pass any thresholds.</p>
</body></html>"""
        result = parser.parse(html, "https://example.com")
        assert "cookies please" not in result.text

    def test_hidden_elements_removed(self, parser):
        result = parser.parse(HIDDEN_ELEMENTS_HTML, "https://example.com")
        assert "hidden and should be removed" not in result.text
        assert "Screen reader hidden" not in result.text
        assert "visible and should be extracted" in result.text

    def test_content_preserved(self, parser):
        result = parser.parse(NOISY_HTML, "https://example.com")
        assert "actual content" in result.text
        assert "Point one" in result.text


# --- Content Extraction ---


class TestContentExtraction:
    def test_article_tag_preferred(self, parser):
        result = parser.parse(SIMPLE_HTML, "https://example.com")
        assert "first paragraph" in result.text
        assert result.word_count > 0

    def test_body_fallback(self, parser):
        result = parser.parse(NO_ARTICLE_HTML, "https://example.com")
        assert "does not use article" in result.text

    def test_nav_removed_in_body_fallback(self, parser):
        result = parser.parse(NO_ARTICLE_HTML, "https://example.com")
        assert "Home" not in result.text

    def test_footer_removed_in_body_fallback(self, parser):
        result = parser.parse(NO_ARTICLE_HTML, "https://example.com")
        assert "Site footer" not in result.text

    def test_minimal_html(self, parser):
        result = parser.parse(MINIMAL_HTML, "https://example.com")
        assert "Just a paragraph" in result.text

    def test_main_tag_used(self, parser):
        html = """\
<html><body>
<nav>Nav content</nav>
<main>
<h1>Main Tag</h1>
<p>Content inside main element with enough text to be detected properly by parser.</p>
</main>
</body></html>"""
        result = parser.parse(html, "https://example.com")
        assert "inside main element" in result.text

    def test_role_main_used(self, parser):
        html = """\
<html><body>
<div role="main">
<h1>Role Main</h1>
<p>Content inside role=main div with enough text to be detected properly by parser.</p>
</div>
</body></html>"""
        result = parser.parse(html, "https://example.com")
        assert "role=main div" in result.text


# --- Markdown Output ---


class TestMarkdown:
    def test_heading_atx_style(self, parser):
        result = parser.parse(SIMPLE_HTML, "https://example.com")
        assert "# " in result.markdown

    def test_list_items(self, parser):
        result = parser.parse(NOISY_HTML, "https://example.com")
        assert "- Point one" in result.markdown

    def test_no_excessive_newlines(self, parser):
        result = parser.parse(NOISY_HTML, "https://example.com")
        assert "\n\n\n" not in result.markdown

    def test_markdown_not_empty(self, parser):
        result = parser.parse(SIMPLE_HTML, "https://example.com")
        assert len(result.markdown) > 0


# --- Language Detection ---


class TestLanguageDetection:
    def test_korean(self, parser):
        result = parser.parse(KOREAN_HTML, "https://example.com")
        assert result.language == "ko"

    def test_english(self, parser):
        result = parser.parse(SIMPLE_HTML, "https://example.com")
        assert result.language == "en"

    def test_empty_content(self, parser):
        result = parser.parse("<html><body></body></html>", "https://example.com")
        assert result.language == "en"

    def test_japanese(self, parser):
        html = """\
<html><body><article>
<p>これは日本語のテスト記事です。人工知能技術が急速に発展しています。
自然言語処理の分野で大きな進展が見られています。この技術は様々な産業に影響を与えています。</p>
</article></body></html>"""
        result = parser.parse(html, "https://example.com")
        assert result.language == "ja"


# --- Metadata Extraction ---


class TestMetadata:
    def test_og_description(self, parser):
        result = parser.parse(NOISY_HTML, "https://example.com")
        assert result.metadata.get("description") == "A meta description"

    def test_author(self, parser):
        result = parser.parse(NOISY_HTML, "https://example.com")
        assert result.metadata.get("author") == "Test Author"

    def test_domain(self, parser):
        result = parser.parse(SIMPLE_HTML, "https://example.com/path")
        assert result.metadata["domain"] == "example.com"

    def test_url_preserved(self, parser):
        result = parser.parse(SIMPLE_HTML, "https://example.com/article/123")
        assert result.metadata["url"] == "https://example.com/article/123"
        assert result.source_url == "https://example.com/article/123"

    def test_published_date(self, parser):
        html = """\
<html>
<head><meta property="article:published_time" content="2024-01-15T10:00:00Z"></head>
<body><article><p>Content with enough text to be detected properly.</p></article></body>
</html>"""
        result = parser.parse(html, "https://example.com")
        assert result.metadata.get("published") == "2024-01-15T10:00:00Z"
