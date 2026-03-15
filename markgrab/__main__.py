"""CLI entry point — python -m markgrab or `markgrab` command."""

import argparse
import asyncio
import json
import sys

from markgrab import extract


def main():
    parser = argparse.ArgumentParser(
        prog="markgrab",
        description="MarkGrab — extract web content as LLM-ready markdown",
    )
    parser.add_argument("url", help="URL to extract content from")
    parser.add_argument("--max-chars", type=int, default=50_000, help="Max output characters (default: 50000)")
    parser.add_argument("--browser", action="store_true", help="Force Playwright browser rendering")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds (default: 30)")
    parser.add_argument("--proxy", help="Proxy URL (e.g., http://proxy:8080)")
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "text", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    try:
        result = asyncio.run(extract(
            args.url,
            max_chars=args.max_chars,
            use_browser=args.browser,
            timeout=args.timeout,
            proxy=args.proxy,
        ))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = {
            "title": result.title,
            "text": result.text,
            "markdown": result.markdown,
            "word_count": result.word_count,
            "language": result.language,
            "content_type": result.content_type,
            "source_url": result.source_url,
            "metadata": result.metadata,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif args.format == "text":
        if result.title:
            print(f"Title: {result.title}")
            print(f"Words: {result.word_count} | Language: {result.language} | Type: {result.content_type}")
            print("---")
        print(result.text)
    else:
        if result.title:
            print(f"# {result.title}")
            print(f"<!-- words: {result.word_count} | lang: {result.language} | type: {result.content_type} -->")
            print()
        print(result.markdown)


if __name__ == "__main__":
    main()
