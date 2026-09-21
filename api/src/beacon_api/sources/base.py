from abc import ABC, abstractmethod

import httpx

from ..models import NewsItem


class NewsSource(ABC):
    """One upstream feed, normalised into `NewsItem`.

    Adapters own their own request shape and parsing. Everything after that -
    caching, de-duplication, ordering - belongs to `NewsService`.
    """

    slug: str
    label: str
    category: str

    @abstractmethod
    async def fetch(self, client: httpx.AsyncClient, limit: int) -> list[NewsItem]:
        """Return up to `limit` items, newest first.

        Raises `SourceError` when the upstream feed cannot be read or parsed.
        """


class SourceError(RuntimeError):
    """An upstream feed was unreachable or returned something unusable."""

    def __init__(self, slug: str, reason: str) -> None:
        super().__init__(f"{slug}: {reason}")
        self.slug = slug
        self.reason = reason
