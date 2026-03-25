# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
