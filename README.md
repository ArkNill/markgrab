# MarkGrab

Universal web content extraction — any URL to LLM-ready markdown.

```python
from markgrab import extract

result = await extract("https://example.com/article")
print(result.markdown)    # clean markdown
print(result.title)       # "Article Title"
print(result.word_count)  # 1234
print(result.language)    # "en"
```

## Features

- **HTML** — BeautifulSoup + content density filtering (removes nav, sidebar, ads)
- **YouTube** — transcript extraction with timestamps
- **PDF** — text extraction with page structure
- **DOCX** — paragraph and heading extraction
- **Auto-fallback** — tries lightweight httpx first, falls back to Playwright for JS-heavy pages
- **Async-first** — built on httpx and Playwright async APIs

## Install

```bash
pip install markgrab
```

Optional extras for specific content types:

```bash
pip install "markgrab[browser]"    # Playwright for JS-rendered pages
pip install "markgrab[youtube]"    # YouTube transcript extraction
pip install "markgrab[pdf]"       # PDF text extraction
pip install "markgrab[docx]"      # DOCX text extraction
pip install "markgrab[all]"       # everything
```

## Usage

### Python API

```python
import asyncio
from markgrab import extract

async def main():
    # HTML (auto-detects content type)
    result = await extract("https://example.com/article")

    # YouTube transcript
    result = await extract("https://youtube.com/watch?v=dQw4w9WgXcQ")

    # PDF
    result = await extract("https://arxiv.org/pdf/1706.03762")

    # Options
    result = await extract(
        "https://example.com",
        max_chars=30_000,       # limit output length (default: 50K)
        use_browser=True,       # force Playwright rendering
        stealth=True,           # anti-bot stealth scripts (opt-in)
        timeout=60.0,           # request timeout in seconds
        proxy="http://proxy:8080",
    )

asyncio.run(main())
```

### CLI

```bash
markgrab https://example.com                     # markdown output
markgrab https://example.com -f text             # plain text
markgrab https://example.com -f json             # structured JSON
markgrab https://example.com --browser           # force browser rendering
markgrab https://example.com --max-chars 10000   # limit output
```

### ExtractResult

```python
result.title        # page title
result.text         # plain text
result.markdown     # LLM-ready markdown
result.word_count   # word count
result.language     # detected language ("en", "ko", ...)
result.content_type # "article", "video", "pdf", "docx"
result.source_url   # final URL (after redirects)
result.metadata     # extra metadata (video_id, page_count, etc.)
```

## How it works

```
markgrab.extract(url)
    1. Detect content type (URL pattern)
    2. Fetch content (httpx first, Playwright fallback)
    3. Parse (HTML/YouTube/PDF/DOCX)
    4. Filter (noise removal + content density + truncation)
    5. Return ExtractResult
```

For HTML pages, if the initial httpx fetch yields fewer than 50 words, MarkGrab automatically retries with Playwright to handle JavaScript-rendered content.

## Disclaimer

**This software is provided for legitimate purposes only.** By using MarkGrab, you agree to the following:

- **robots.txt**: MarkGrab does **not** check or enforce `robots.txt`. Users are solely responsible for checking and respecting `robots.txt` directives and the terms of service of any website they access.

- **Rate limiting**: MarkGrab does **not** include built-in rate limiting or request throttling. Users must implement their own rate limiting to avoid overloading target servers. Abusive request patterns may violate applicable laws and website terms of service.

- **YouTube transcripts**: YouTube transcript extraction relies on the third-party `youtube-transcript-api` library, which uses YouTube's internal (unofficial) caption API. This may not comply with YouTube's Terms of Service. Use at your own discretion and risk.

- **Stealth mode**: The optional `stealth=True` feature modifies browser fingerprinting signals to reduce bot detection. This feature is intended for legitimate use cases such as testing, research, and accessing content that is publicly available to regular browser users. Users are responsible for ensuring their use complies with applicable laws and the terms of service of target websites.

- **Legal compliance**: Users are responsible for ensuring that their use of MarkGrab complies with all applicable laws, including but not limited to the Computer Fraud and Abuse Act (CFAA), the Digital Millennium Copyright Act (DMCA), GDPR, and equivalent legislation in their jurisdiction.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. See the [LICENSE](LICENSE) file for the full MIT license text.

## License

[MIT](LICENSE)
