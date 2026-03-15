# MarkGrab

> [English](README.md)

범용 웹 콘텐츠 추출 — 어떤 URL이든 LLM-ready 마크다운으로 변환합니다.

```python
from markgrab import extract

result = await extract("https://example.com/article")
print(result.markdown)    # 정제된 마크다운
print(result.title)       # "기사 제목"
print(result.word_count)  # 1234
print(result.language)    # "ko"
```

## 기능

- **HTML** — BeautifulSoup + 본문 밀도 필터링 (네비게이션, 사이드바, 광고 제거)
- **YouTube** — 타임스탬프 포함 자막 추출
- **PDF** — 페이지 구조 보존 텍스트 추출
- **DOCX** — 문단/헤딩 구조 인식 추출
- **자동 폴백** — 경량 httpx로 먼저 시도, JS 렌더링 필요 시 Playwright 자동 전환
- **Async 기반** — httpx와 Playwright 비동기 API 활용

## 설치

```bash
pip install markgrab
```

콘텐츠 타입별 선택 설치:

```bash
pip install "markgrab[browser]"    # JS 렌더링 페이지용 Playwright
pip install "markgrab[youtube]"    # YouTube 자막 추출
pip install "markgrab[pdf]"       # PDF 텍스트 추출
pip install "markgrab[docx]"      # DOCX 텍스트 추출
pip install "markgrab[all]"       # 전체 설치
```

## 사용법

### Python API

```python
import asyncio
from markgrab import extract

async def main():
    # HTML (콘텐츠 타입 자동 감지)
    result = await extract("https://example.com/article")

    # YouTube 자막
    result = await extract("https://youtube.com/watch?v=dQw4w9WgXcQ")

    # PDF
    result = await extract("https://arxiv.org/pdf/1706.03762")

    # 옵션
    result = await extract(
        "https://example.com",
        max_chars=30_000,       # 출력 길이 제한 (기본값: 50K)
        use_browser=True,       # Playwright 브라우저 강제 사용
        stealth=True,           # 안티봇 스텔스 스크립트 (opt-in)
        timeout=60.0,           # 요청 타임아웃 (초)
        proxy="http://proxy:8080",
    )

asyncio.run(main())
```

### CLI

```bash
markgrab https://example.com                     # 마크다운 출력
markgrab https://example.com -f text             # 일반 텍스트
markgrab https://example.com -f json             # 구조화된 JSON
markgrab https://example.com --browser           # 브라우저 렌더링 강제
markgrab https://example.com --max-chars 10000   # 출력 길이 제한
```

### ExtractResult

```python
result.title        # 페이지 제목
result.text         # 일반 텍스트
result.markdown     # LLM-ready 마크다운
result.word_count   # 단어 수
result.language     # 감지된 언어 ("en", "ko", ...)
result.content_type # "article", "video", "pdf", "docx"
result.source_url   # 최종 URL (리다이렉트 후)
result.metadata     # 추가 메타데이터 (video_id, page_count 등)
```

## 동작 원리

```
markgrab.extract(url)
    1. 콘텐츠 타입 감지 (URL 패턴)
    2. 콘텐츠 획득 (httpx 우선, Playwright 폴백)
    3. 파싱 (HTML/YouTube/PDF/DOCX)
    4. 필터링 (노이즈 제거 + 본문 밀도 필터 + 길이 제한)
    5. ExtractResult 반환
```

HTML 페이지의 경우, httpx로 가져온 결과가 50단어 미만이면 JavaScript 렌더링이 필요한 페이지로 판단하여 Playwright로 자동 재시도합니다.

## 면책 조항

**이 소프트웨어는 합법적인 목적으로만 제공됩니다.** MarkGrab을 사용함으로써 다음 사항에 동의하는 것으로 간주됩니다:

- **robots.txt**: MarkGrab은 `robots.txt`를 확인하거나 강제하지 **않습니다**. 사용자는 접근하는 웹사이트의 `robots.txt` 지침과 이용약관을 직접 확인하고 준수할 책임이 있습니다.

- **속도 제한**: MarkGrab에는 내장된 속도 제한이나 요청 스로틀링이 **없습니다**. 대상 서버에 과부하를 주지 않도록 사용자가 직접 속도 제한을 구현해야 합니다. 남용적인 요청 패턴은 관련 법률 및 웹사이트 이용약관을 위반할 수 있습니다.

- **YouTube 자막**: YouTube 자막 추출은 YouTube의 내부(비공식) 자막 API를 사용하는 서드파티 라이브러리 `youtube-transcript-api`에 의존합니다. 이는 YouTube 이용약관을 준수하지 않을 수 있습니다. 사용자의 판단과 책임 하에 사용하시기 바랍니다.

- **스텔스 모드**: 선택적 `stealth=True` 기능은 봇 탐지를 줄이기 위해 브라우저 핑거프린트 신호를 수정합니다. 이 기능은 테스트, 연구, 일반 브라우저 사용자에게 공개적으로 제공되는 콘텐츠 접근 등 합법적인 용도를 위한 것입니다. 사용자는 관련 법률 및 대상 웹사이트의 이용약관을 준수할 책임이 있습니다.

- **법적 준수**: 사용자는 컴퓨터 사기 및 남용 방지법(CFAA), 디지털 밀레니엄 저작권법(DMCA), GDPR 및 해당 관할권의 동등한 법률을 포함하되 이에 국한되지 않는 모든 관련 법률을 준수할 책임이 있습니다.

이 소프트웨어는 어떠한 종류의 보증 없이 "있는 그대로" 제공됩니다. 전체 MIT 라이선스 텍스트는 [LICENSE](LICENSE) 파일을 참조하세요.

## 감사의 말

MarkGrab은 우수한 오픈소스 프로젝트와 확립된 기술에서 영감을 받았습니다:

- **[puppeteer-extra-plugin-stealth](https://github.com/nicoleahmed/puppeteer-extra-plugin-stealth)** — webdriver 제거, 플러그인 모킹, WebGL 스푸핑 등 스텔스 회피 패턴의 원류. opt-in `anti_bot/stealth.py` 모듈에 영감을 줌
- **[Mozilla Readability](https://github.com/mozilla/readability)** — 본문 영역 탐지 우선순위 (`article > main > body`) 및 링크 밀도 필터링 개념
- **[Boilerpipe](https://github.com/kohlschutter/boilerpipe)** (Kohlschutter et al., 2010) — 보일러플레이트 제거를 위한 링크 밀도 비율 알고리즘의 학술적 원류
- **[Jina Reader](https://github.com/jina-ai/reader)** — URL→마크다운 추출의 시장 수요를 검증. MarkGrab은 경량 자체 호스팅 대안을 지향

사용 라이브러리: [httpx](https://github.com/encode/httpx), [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/), [markdownify](https://github.com/matthewwithanm/python-markdownify), [Playwright](https://github.com/microsoft/playwright-python), [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api), [pdfplumber](https://github.com/jsvine/pdfplumber), [python-docx](https://github.com/python-openxml/python-docx).

## 라이선스

[MIT](LICENSE)
