"""YouTube parser — extract transcript from YouTube videos."""

import logging
import re
from urllib.parse import parse_qs, urlparse

from markgrab.result import ExtractResult
from markgrab.utils import detect_language

logger = logging.getLogger(__name__)

_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

# Language preference order for transcript fetching
_LANG_PRIORITY = ("en", "ko", "ja", "zh-Hans", "zh-Hant", "de", "fr", "es", "pt")


def _extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    parsed = urlparse(url)

    # youtube.com/watch?v=ID
    if "youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        vid = qs.get("v", [None])[0]
        if vid and _VIDEO_ID_RE.match(vid):
            return vid

    # youtu.be/ID
    if "youtu.be" in parsed.netloc:
        vid = parsed.path.lstrip("/").split("/")[0]
        if vid and _VIDEO_ID_RE.match(vid):
            return vid

    raise ValueError(f"Cannot extract video ID from URL: {url}")


class YouTubeParser:
    """Extract transcript from YouTube videos using youtube-transcript-api."""

    def parse(self, video_id: str, url: str, title: str = "") -> ExtractResult:
        """Parse YouTube transcript.

        Args:
            video_id: YouTube video ID (11 chars).
            url: Original YouTube URL.
            title: Video title (from oEmbed or fallback).
        """
        from youtube_transcript_api import YouTubeTranscriptApi

        ytt = YouTubeTranscriptApi()

        # Try preferred languages, fall back to any available
        transcript = None
        transcript_lang = "en"
        try:
            transcript_list = ytt.list(video_id)
            for lang in _LANG_PRIORITY:
                try:
                    transcript = transcript_list.find_transcript([lang]).fetch()
                    transcript_lang = lang
                    break
                except Exception:
                    continue

            # If no preferred language found, take the first available
            if transcript is None:
                for t in transcript_list:
                    transcript = t.fetch()
                    transcript_lang = t.language_code
                    break
        except Exception:
            # Fallback: direct fetch with language priority
            transcript = ytt.fetch(video_id, languages=_LANG_PRIORITY)
            transcript_lang = "en"

        if transcript is None:
            raise ValueError(f"No transcript available for video: {video_id}")

        # Materialize snippets once (iterator may be single-use)
        snippets = list(transcript)

        # Build text from snippets
        text = "\n".join(s.text for s in snippets)

        # Build markdown with timestamps
        md_lines = []
        if title:
            md_lines.append(f"# {title}\n")
        for s in snippets:
            minutes = int(s.start // 60)
            seconds = int(s.start % 60)
            md_lines.append(f"[{minutes:02d}:{seconds:02d}] {s.text}")
        markdown = "\n".join(md_lines)

        language = detect_language(text) if text else transcript_lang

        return ExtractResult(
            title=title or f"YouTube Video {video_id}",
            text=text,
            markdown=markdown,
            word_count=len(text.split()),
            language=language,
            content_type="video",
            source_url=url,
            metadata={"video_id": video_id, "transcript_language": transcript_lang},
        )
