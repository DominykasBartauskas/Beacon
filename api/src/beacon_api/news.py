import asyncio
import logging
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx

from .data import NEWS
from .models import NewsItem
from .sources import NewsSource, default_sources

logger = logging.getLogger(__name__)


def _canonical_url(url: str) -> str:
    """Host and path only: the same story over http and https is one story."""
    parts = urlsplit(url)
    host = parts.netloc.lower().removeprefix("www.")
    return f"{host}{parts.path.rstrip('/')}"


def _dedupe_key(item: NewsItem) -> str:
    if item.url:
        return _canonical_url(item.url)
    return " ".join(item.title.lower().split())


def dedupe(items: list[NewsItem]) -> list[NewsItem]:
    """Drop repeats, keeping the earliest-published copy of each story."""
    keep: dict[str, NewsItem] = {}
    for item in items:
        key = _dedupe_key(item)
        existing = keep.get(key)
        if existing is None or item.published_at < existing.published_at:
            keep[key] = item
    return sorted(keep.values(), key=lambda item: item.published_at, reverse=True)


class NewsService:
    """Aggregates the configured sources behind a short-lived cache.

    Upstream failures are never fatal: a source that raises is skipped, and if
    every source fails the sample feed is served so the dashboard stays up.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        sources: list[NewsSource] | None = None,
        *,
        enabled: bool = True,
        cache_ttl_seconds: int = 900,
        fetch_limit: int = 30,
        github_token: str = "",
        x_bearer_token: str = "",
    ) -> None:
        self._client = client
        self._sources = default_sources(github_token, x_bearer_token) if sources is None else sources
        self._enabled = enabled
        self._cache_ttl_seconds = cache_ttl_seconds
        self._fetch_limit = fetch_limit
        self._cached: list[NewsItem] | None = None
        self._cached_at: datetime | None = None
        self._lock = asyncio.Lock()

    @property
    def fallback(self) -> list[NewsItem]:
        return list(NEWS)

    def _cache_is_fresh(self) -> bool:
        if self._cached is None or self._cached_at is None:
            return False
        age = (datetime.now(UTC) - self._cached_at).total_seconds()
        return age < self._cache_ttl_seconds

    async def items(self) -> list[NewsItem]:
        if not self._enabled or not self._sources:
            return self.fallback

        async with self._lock:
            if self._cache_is_fresh() and self._cached is not None:
                return self._cached

            fetched = await self._fetch_all()
            if not fetched:
                return self._cached if self._cached is not None else self.fallback

            self._cached = fetched
            self._cached_at = datetime.now(UTC)
            return fetched

    async def _fetch_all(self) -> list[NewsItem]:
        results = await asyncio.gather(
            *(source.fetch(self._client, self._fetch_limit) for source in self._sources),
            return_exceptions=True,
        )

        collected: list[NewsItem] = []
        for source, result in zip(self._sources, results, strict=True):
            if isinstance(result, BaseException):
                logger.warning("source %s failed: %s", source.slug, result)
                continue
            collected.extend(result)
        return dedupe(collected)
