"""Tests for DocxParser."""

import sys
from unittest.mock import MagicMock, patch

from markgrab.parser.docx import DocxParser


def _make_mock_paragraph(text, style_name="Normal"):
    """Create a mock paragraph."""
    para = MagicMock()
    para.text = text
    style = MagicMock()
    style.name = style_name
    para.style = style
    return para


def _make_mock_doc(paragraphs, title="", author="", created=None, modified=None, subject=""):
    """Create a mock Document."""
    mock_doc = MagicMock()
    mock_doc.paragraphs = paragraphs

    props = MagicMock()
    props.title = title
    props.author = author
    props.created = created
    props.modified = modified
    props.subject = subject
    mock_doc.core_properties = props

    return mock_doc


def _patch_docx(mock_doc):
    """Patch docx module for local import inside DocxParser.parse()."""
    mock_docx_module = MagicMock()
    mock_docx_module.Document = MagicMock(return_value=mock_doc)
    return patch.dict(sys.modules, {"docx": mock_docx_module})


def test_parse_basic():
    paragraphs = [
        _make_mock_paragraph("This is the first paragraph of the document."),
        _make_mock_paragraph("This is the second paragraph with more content."),
    ]
    doc = _make_mock_doc(paragraphs, title="Test Document")

    with _patch_docx(doc):
        result = DocxParser().parse(b"fake docx data", url="https://example.com/doc.docx")

    assert result.title == "Test Document"
    assert "first paragraph" in result.text
    assert "second paragraph" in result.text
    assert result.content_type == "document"
    assert result.word_count > 0


def test_parse_with_headings():
    paragraphs = [
        _make_mock_paragraph("Introduction", "Heading 1"),
        _make_mock_paragraph("This is the introduction text."),
        _make_mock_paragraph("Details", "Heading 2"),
        _make_mock_paragraph("Here are some details."),
    ]
    doc = _make_mock_doc(paragraphs)

    with _patch_docx(doc):
        result = DocxParser().parse(b"data", url="https://example.com/doc.docx")

    assert "# Introduction" in result.markdown
    assert "## Details" in result.markdown


def test_parse_with_lists():
    paragraphs = [
        _make_mock_paragraph("First item", "List Paragraph"),
        _make_mock_paragraph("Second item", "List Paragraph"),
        _make_mock_paragraph("Regular text after list."),
    ]
    doc = _make_mock_doc(paragraphs)

    with _patch_docx(doc):
        result = DocxParser().parse(b"data", url="https://example.com/doc.docx")

    assert "- First item" in result.markdown
    assert "- Second item" in result.markdown


def test_parse_empty_paragraphs_skipped():
    paragraphs = [
        _make_mock_paragraph("Real content."),
        _make_mock_paragraph(""),
        _make_mock_paragraph("   "),
        _make_mock_paragraph("More content."),
    ]
    doc = _make_mock_doc(paragraphs)

    with _patch_docx(doc):
        result = DocxParser().parse(b"data", url="https://example.com/doc.docx")

    assert "Real content" in result.text
    assert "More content" in result.text
    assert result.word_count == 4


def test_parse_no_title_fallback():
    paragraphs = [_make_mock_paragraph("Some content.")]
    doc = _make_mock_doc(paragraphs, title="")

    with _patch_docx(doc):
        result = DocxParser().parse(b"data", url="https://example.com/doc.docx")

    assert result.title == "DOCX Document"


def test_parse_metadata_extraction():
    paragraphs = [_make_mock_paragraph("Content.")]
    doc = _make_mock_doc(paragraphs, title="Report", author="Jane Smith", subject="Annual Report")

    with _patch_docx(doc):
        result = DocxParser().parse(b"data", url="https://example.com/report.docx")

    assert result.metadata["author"] == "Jane Smith"
    assert result.metadata["subject"] == "Annual Report"


def test_parse_korean_content():
    paragraphs = [_make_mock_paragraph(
        "인공지능 기술이 빠르게 발전하고 있습니다. 최근 대규모 언어 모델의 등장으로 "
        "자연어 처리 분야에서 큰 진전이 이루어졌습니다. 이러한 기술 발전은 다양한 "
        "산업 분야에 혁신을 가져오고 있습니다."
    )]
    doc = _make_mock_doc(paragraphs)

    with _patch_docx(doc):
        result = DocxParser().parse(b"data", url="https://example.com/doc.docx")

    assert result.language == "ko"


def test_parse_source_url_preserved():
    paragraphs = [_make_mock_paragraph("Content.")]
    doc = _make_mock_doc(paragraphs)

    with _patch_docx(doc):
        result = DocxParser().parse(b"data", url="https://example.com/final.docx")

    assert result.source_url == "https://example.com/final.docx"
