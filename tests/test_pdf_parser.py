"""Tests for PdfParser."""

import sys
from io import BytesIO
from unittest.mock import MagicMock, patch

from markgrab.parser.pdf import PdfParser


def _make_mock_pdf(pages_text, metadata=None):
    """Create a mock pdfplumber PDF object."""
    mock_pages = []
    for text in pages_text:
        page = MagicMock()
        page.extract_text = MagicMock(return_value=text)
        mock_pages.append(page)

    pdf = MagicMock()
    pdf.pages = mock_pages
    pdf.metadata = metadata or {}
    pdf.__enter__ = MagicMock(return_value=pdf)
    pdf.__exit__ = MagicMock(return_value=False)
    return pdf


def _patch_pdfplumber(mock_pdf):
    """Patch pdfplumber.open to return mock PDF."""
    mock_module = MagicMock()
    mock_module.open = MagicMock(return_value=mock_pdf)
    return patch.dict(sys.modules, {"pdfplumber": mock_module})


def test_parse_single_page():
    pdf = _make_mock_pdf(["This is a simple PDF document with some text content."])

    with _patch_pdfplumber(pdf):
        result = PdfParser().parse(b"%PDF-1.4 fake data", url="https://example.com/doc.pdf")

    assert "simple PDF document" in result.text
    assert result.content_type == "pdf"
    assert result.source_url == "https://example.com/doc.pdf"
    assert result.word_count > 0


def test_parse_multi_page():
    pdf = _make_mock_pdf([
        "First page content about machine learning.",
        "Second page with more detailed information.",
        "Third page conclusion and references.",
    ])

    with _patch_pdfplumber(pdf):
        result = PdfParser().parse(b"data", url="https://example.com/paper.pdf")

    assert "First page" in result.text
    assert "Third page" in result.text
    assert result.metadata["page_count"] == 3
    assert "## Page 1" in result.markdown
    assert "## Page 3" in result.markdown


def test_parse_with_title_metadata():
    pdf = _make_mock_pdf(
        ["Content here."],
        metadata={"Title": "Research Paper 2024", "Author": "John Doe"},
    )

    with _patch_pdfplumber(pdf):
        result = PdfParser().parse(b"data", url="https://example.com/paper.pdf")

    assert result.title == "Research Paper 2024"
    assert result.metadata["author"] == "John Doe"


def test_parse_no_title_fallback():
    pdf = _make_mock_pdf(["Some content."], metadata={})

    with _patch_pdfplumber(pdf):
        result = PdfParser().parse(b"data", url="https://example.com/doc.pdf")

    assert result.title == "PDF Document"


def test_parse_empty_pages_skipped():
    pdf = _make_mock_pdf(["Real content here.", "", "   ", "More content."])

    with _patch_pdfplumber(pdf):
        result = PdfParser().parse(b"data", url="https://example.com/doc.pdf")

    assert "Real content" in result.text
    assert "More content" in result.text
    assert result.metadata["page_count"] == 2


def test_parse_korean_content():
    pdf = _make_mock_pdf([(
        "인공지능 기술이 빠르게 발전하고 있습니다. 최근 대규모 언어 모델의 등장으로 "
        "자연어 처리 분야에서 큰 진전이 이루어졌습니다. 이러한 기술 발전은 다양한 "
        "산업 분야에 혁신을 가져오고 있습니다."
    )])

    with _patch_pdfplumber(pdf):
        result = PdfParser().parse(b"data", url="https://example.com/doc.pdf")

    assert result.language == "ko"


def test_parse_single_page_no_page_headers():
    pdf = _make_mock_pdf(["Only one page of content."])

    with _patch_pdfplumber(pdf):
        result = PdfParser().parse(b"data", url="https://example.com/doc.pdf")

    assert "## Page" not in result.markdown


def test_context_manager_used():
    """pdfplumber uses context manager — verify __enter__/__exit__ called."""
    pdf = _make_mock_pdf(["Content."])

    with _patch_pdfplumber(pdf):
        PdfParser().parse(b"data", url="https://example.com/doc.pdf")

    pdf.__enter__.assert_called_once()
    pdf.__exit__.assert_called_once()
