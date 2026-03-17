"""MarkGrab MCP server — expose extract as an MCP tool for Claude Code."""

import asyncio
import json

from fastmcp import FastMCP

from markgrab.core import extract

mcp = FastMCP(
    "markgrab",
    instructions="Universal web content extraction — any URL to LLM-ready markdown",
)


@mcp.tool()
async def extract_url(
    url: str,
    max_chars: int = 50_000,
    use_browser: bool = False,
    output_format: str = "markdown",
) -> str:
    """Extract content from a URL and return clean, LLM-ready text.

    Supports HTML pages, YouTube transcripts, PDF, and DOCX.
    Auto-detects content type from URL. Falls back to browser rendering
    for JS-heavy pages when Playwright is installed.

    Args:
        url: Target URL to extract content from.
        max_chars: Maximum characters in output (default: 50000).
        use_browser: Force Playwright browser rendering for JS-heavy pages.
        output_format: "markdown" (default), "text", or "json".
    """
    result = await extract(
        url,
        max_chars=max_chars,
        use_browser=use_browser,
    )

    if output_format == "json":
        return json.dumps(
            {
                "title": result.title,
                "markdown": result.markdown,
                "word_count": result.word_count,
                "language": result.language,
                "content_type": result.content_type,
                "source_url": result.source_url,
            },
            ensure_ascii=False,
        )
    elif output_format == "text":
        return result.text
    else:
        return result.markdown


@mcp.tool()
async def extract_multiple(
    urls: list[str],
    max_chars: int = 30_000,
) -> str:
    """Extract content from multiple URLs at once.

    Returns a JSON array with results for each URL.

    Args:
        urls: List of URLs to extract content from.
        max_chars: Maximum characters per URL (default: 30000).
    """
    results = []
    for url in urls:
        try:
            result = await extract(url, max_chars=max_chars)
            results.append({
                "url": url,
                "title": result.title,
                "word_count": result.word_count,
                "language": result.language,
                "markdown": result.markdown,
            })
        except Exception as e:
            results.append({"url": url, "error": str(e)})

    return json.dumps(results, ensure_ascii=False)


def main():
    """Run the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
