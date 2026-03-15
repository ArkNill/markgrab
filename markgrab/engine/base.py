"""Engine base — content fetching abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class FetchResult:
    """Raw result from fetching a URL."""

    html: str
    status_code: int
    content_type: str
    final_url: str


# Shared User-Agent pool — used by HttpEngine, core._fetch_bytes, etc.
USER_AGENTS = [
    (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
]


class Engine(ABC):
    """Abstract base for content fetching engines."""

    def __init__(self, *, proxy: str | None = None):
        self.proxy = proxy

    @abstractmethod
    async def fetch(self, url: str, *, timeout: float = 30.0) -> FetchResult:
        ...
