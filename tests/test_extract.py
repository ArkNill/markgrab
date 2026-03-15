"""Integration tests for extract()."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from markgrab import ExtractResult, extract
from markgrab.engine.base import FetchResult

# All test HTML must have >= 50 words to avoid triggering browser fallback

_ARTICLE_BODY = (
    "This is a comprehensive test article with enough content to be extracted "
    "properly by the parser. It includes multiple sentences that provide sufficient "
    "word count to pass the minimum threshold for content validation. The article "
    "discusses various topics and contains detailed information that makes it "
    "clearly a real piece of content rather than an empty placeholder page."
)

_KOREAN_BODY = (
    "인공지능 기술이 빠르게 발전하고 있습니다. 최근 대규모 언어 모델의 등장으로 "
    "자연어 처리 분야에서 큰 진전이 이루어졌습니다. 이러한 기술 발전은 다양한 "
    "산업 분야에 혁신을 가져오고 있으며, 앞으로 더 많은 변화가 예상됩니다. "
    "한국에서도 AI 관련 투자가 크게 증가하고 있으며 글로벌 시장에서의 경쟁력을 "
    "확보하기 위한 노력이 계속되고 있습니다. 기업들은 AI 기반 서비스를 개발하고 "
    "데이터 활용 능력을 강화하는 데 집중하고 있습니다."
)


def _mock_engine(html: str, url: str = "https://example.com"):
    """Create a mock engine that returns given HTML."""
    engine = AsyncMock()
    engine.fetch = AsyncMock(return_value=FetchResult(
        html=html,
        status_code=200,
        content_type="text/html",
        final_url=url,
    ))
    return engine


@pytest.mark.asyncio
async def test_extract_simple():
    html = f"""\
<html><head><title>Test</title></head>
<body><article>
<h1>Hello</h1>
<p>{_ARTICLE_BODY}</p>
</article></body></html>"""
    engine = _mock_engine(html)
    result = await extract("https://example.com", engine=engine)

    assert isinstance(result, ExtractResult)
    assert result.title == "Test"
    assert "test article" in result.text.lower()
    assert result.word_count >= 50
    assert result.language == "en"
    assert result.content_type == "article"


@pytest.mark.asyncio
async def test_extract_with_max_chars():
    long_content = "<p>" + ("word " * 20000) + "</p>"
    html = f"<html><body><article><h1>Long</h1>{long_content}</article></body></html>"
    engine = _mock_engine(html)
    result = await extract("https://example.com", engine=engine, max_chars=500)

    assert len(result.text) < 600
    assert "[truncated]" in result.text


@pytest.mark.asyncio
async def test_extract_youtube():
    """YouTube URL → YouTubeParser (mocked transcript API)."""
    mock_snippet = MagicMock()
    mock_snippet.text = (
        "This is a test transcript with enough words to verify that the YouTube"
        " parser integration works correctly in the full extract pipeline"
    )
    mock_snippet.start = 0.0
    mock_snippet.duration = 10.0

    mock_fetched = MagicMock()
    mock_fetched.__iter__ = MagicMock(return_value=iter([mock_snippet]))

    mock_transcript = MagicMock()
    mock_transcript.fetch = MagicMock(return_value=mock_fetched)
    mock_transcript.language_code = "en"

    mock_transcript_list = MagicMock()
    mock_transcript_list.find_transcript = MagicMock(return_value=mock_transcript)
    mock_transcript_list.__iter__ = MagicMock(return_value=iter([mock_transcript]))

    mock_api_instance = MagicMock()
    mock_api_instance.list = MagicMock(return_value=mock_transcript_list)

    mock_ytt_module = MagicMock()
    mock_ytt_module.YouTubeTranscriptApi = MagicMock(return_value=mock_api_instance)

    with (
        patch.dict(sys.modules, {"youtube_transcript_api": mock_ytt_module}),
        patch("markgrab.core._fetch_youtube_title", new_callable=AsyncMock, return_value="Test Video"),
    ):
        result = await extract("https://youtube.com/watch?v=dQw4w9WgXcQ")

    assert result.content_type == "video"
    assert "test transcript" in result.text.lower()
    assert result.metadata["video_id"] == "dQw4w9WgXcQ"


@pytest.mark.asyncio
async def test_extract_pdf_url():
    """PDF URL → PdfParser (mocked pdfplumber)."""
    mock_page = MagicMock()
    mock_page.extract_text = MagicMock(return_value="This is extracted PDF text content.")

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.metadata = {"Title": "Test PDF"}
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    mock_pdfplumber = MagicMock()
    mock_pdfplumber.open = MagicMock(return_value=mock_pdf)

    with (
        patch.dict(sys.modules, {"pdfplumber": mock_pdfplumber}),
        patch("markgrab.core._fetch_bytes", new_callable=AsyncMock, return_value=(
            b"%PDF-data", "https://example.com/paper.pdf"
        )),
    ):
        result = await extract("https://example.com/paper.pdf")

    assert result.content_type == "pdf"
    assert "PDF text content" in result.text
    assert result.title == "Test PDF"


@pytest.mark.asyncio
async def test_extract_pdf_content_type():
    """HTML URL that returns application/pdf Content-Type → PdfParser."""
    mock_page = MagicMock()
    mock_page.extract_text = MagicMock(return_value="PDF content from content-type detection.")

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.metadata = {}
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    mock_pdfplumber = MagicMock()
    mock_pdfplumber.open = MagicMock(return_value=mock_pdf)

    engine = AsyncMock()
    engine.fetch = AsyncMock(return_value=FetchResult(
        html="%PDF-1.4...",
        status_code=200,
        content_type="application/pdf",
        final_url="https://example.com/doc",
    ))

    with (
        patch.dict(sys.modules, {"pdfplumber": mock_pdfplumber}),
        patch("markgrab.core._fetch_bytes", new_callable=AsyncMock, return_value=(
            b"%PDF-data", "https://example.com/doc"
        )),
    ):
        result = await extract("https://example.com/doc", engine=engine)

    assert result.content_type == "pdf"


@pytest.mark.asyncio
async def test_extract_browser_requires_playwright():
    with patch("markgrab.core._BROWSER_AVAILABLE", False):
        with pytest.raises(ImportError, match="Playwright"):
            await extract("https://example.com", use_browser=True)


@pytest.mark.asyncio
async def test_extract_preserves_source_url():
    html = f"""\
<html><body><article>
<h1>Test</h1>
<p>{_ARTICLE_BODY}</p>
</article></body></html>"""
    engine = _mock_engine(html, url="https://example.com/final")
    result = await extract("https://example.com/redirect", engine=engine)

    assert result.source_url == "https://example.com/final"


@pytest.mark.asyncio
async def test_extract_korean_content():
    html = f"""\
<html><body><article>
<h1>테스트</h1>
<p>{_KOREAN_BODY}</p>
</article></body></html>"""
    engine = _mock_engine(html)
    result = await extract("https://example.com", engine=engine)

    assert result.language == "ko"
    assert result.word_count > 0
