# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-24

### Added
- `extract_batch()` for thread-safe concurrent URL extraction using asyncio
  - `asyncio.Semaphore` + `asyncio.gather` (no threads — Playwright deadlock-free)
  - Per-domain rate limiting via `asyncio.Lock`
  - Per-URL hard timeout via `asyncio.wait_for`
  - Configurable `max_concurrent`, `domain_delay`, `per_url_timeout`
- 10 new batch tests (124 total)

### Changed
- MCP `extract_multiple()` now uses `extract_batch()` for parallel extraction (was sequential)
- Publish workflow creates GitHub Release automatically

## [0.1.3] - 2026-04-10

### Added
- Locale auto-detection from URL hostname TLD (`.kr` → ko-KR, `.jp` → ja-JP)
- CloudFlare/bot challenge retry (up to 3 retries for suspiciously small pages)
- `llms.txt` and `llms-full.txt` for LLM discoverability
- PyPI project-urls and QuartzUnit ecosystem link

## [0.1.2] - 2026-03-17

### Added
- CSS class detection for improved content extraction accuracy
- Locale support for multi-language content handling
- Chrome User-Agent header for better site compatibility
- MCP server module with 2 tools (`extract_url`, `extract_multiple`)
- MCP registry metadata (`server.json`)

## [0.1.1] - 2026-03-16

### Fixed
- Preserve text after mixed `<br>` and `<br />` tags

## [0.1.0] - 2026-03-15

### Added
- Initial release
- HTML extraction with BeautifulSoup + content density filtering
- YouTube transcript extraction with multi-language support
- PDF text extraction with page structure
- DOCX paragraph and heading extraction
- Auto-fallback: lightweight httpx first, Playwright for JS-heavy pages
- Async-first architecture built on httpx and Playwright
- Opt-in anti-bot stealth scripts for browser engine
- CLI interface for terminal usage
- 112 unit tests
- Korean documentation (`README.ko.md`)
