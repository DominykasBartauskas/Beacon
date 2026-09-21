import asyncio
import re
from datetime import datetime
from xml.etree import ElementTree

import httpx

from ..models import NewsItem
from .base import NewsSource, SourceError

ATOM = "{http://www.w3.org/2005/Atom}"
FEED_URL = "https://export.arxiv.org/api/query"
DEFAULT_CATEGORIES = ("cs.AI", "cs.LG", "cs.CL")
WHITESPACE = re.compile(r"\s+")
# arXiv answers bursts with 406 rather than 429; it asks for a few seconds between calls.
THROTTLED_STATUSES = frozenset({406, 429, 503})
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 3.0


def _clean(text: str | None) -> str:
    return WHITESPACE.sub(" ", (text or "").strip())


def _summarise(text: str, limit: int = 240) -> str:
    summary = _clean(text)
    if len(summary) <= limit:
        return summary
    head, _, _ = summary[:limit].rpartition(" ")
    return f"{head or summary[:limit]}…"


class ArxivSource(NewsSource):
    """Recent submissions from arXiv's Atom API.

    arXiv asks for no more than one request every few seconds, which the
    service-level cache keeps us well inside.
    """

    slug = "arxiv"
    label = "arXiv"
    category = "AI Research"

    def __init__(self, categories: tuple[str, ...] = DEFAULT_CATEGORIES) -> None:
        self.categories = categories

    @property
    def query(self) -> str:
        return " OR ".join(f"cat:{category}" for category in self.categories)

    async def fetch(self, client: httpx.AsyncClient, limit: int) -> list[NewsItem]:
        params = {
            "search_query": self.query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(limit),
        }

        last_error: Exception | None = None
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = await client.get(FEED_URL, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                last_error = error
                if error.response.status_code not in THROTTLED_STATUSES:
                    raise SourceError(self.slug, str(error)) from error
            except httpx.HTTPError as error:
                raise SourceError(self.slug, str(error)) from error
            else:
                return self.parse(response.text)

            if attempt + 1 < RETRY_ATTEMPTS:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))

        raise SourceError(self.slug, f"throttled after {RETRY_ATTEMPTS} attempts: {last_error}")

    def parse(self, payload: str) -> list[NewsItem]:
        try:
            feed = ElementTree.fromstring(payload)
        except ElementTree.ParseError as error:
            raise SourceError(self.slug, f"malformed feed: {error}") from error

        items: list[NewsItem] = []
        for entry in feed.iter(f"{ATOM}entry"):
            item = self._entry_to_item(entry)
            if item is not None:
                items.append(item)
        return items

    def _entry_to_item(self, entry: ElementTree.Element) -> NewsItem | None:
        entry_id = _clean(entry.findtext(f"{ATOM}id"))
        title = _clean(entry.findtext(f"{ATOM}title"))
        published = self._published(entry)
        if not entry_id or not title or published is None:
            return None

        return NewsItem(
            id=f"{self.slug}:{entry_id.rsplit('/', 1)[-1]}",
            title=title,
            summary=_summarise(entry.findtext(f"{ATOM}summary") or ""),
            source=self.label,
            published_at=published,
            category=self.category,
            url=entry_id or None,
        )

    @staticmethod
    def _published(entry: ElementTree.Element) -> datetime | None:
        raw = _clean(entry.findtext(f"{ATOM}published"))
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
