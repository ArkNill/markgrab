"""MarkGrab — Universal web content extraction."""

from markgrab.core import extract, extract_batch
from markgrab.result import ExtractResult

__all__ = ["extract", "extract_batch", "ExtractResult"]
__version__ = "0.2.0"
