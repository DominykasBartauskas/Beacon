import asyncio
import html
import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

from ..categories import AI_PRODUCTS, classify
from ..models import NewsItem
from .base import NewsSource, SourceError

ATOM = "{http://www.w3.org/2005/Atom}"
TAGS = re.compile(r"<[^>]+>")
WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class Feed:
    slug: str
    label: str
    url: str


# Anthropic publishes no public feed; every documented path 404s, so it is absent.
DEFAULT_FEEDS = (
    Feed("openai", "OpenAI", "https://openai.com/news/rss.xml"),
    Feed("deepmind", "Google DeepMind", "https://deepmind.google/blog/rss.xml"),
    Feed("huggingface-blog", "Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
    Feed("google-ai", "Google AI", "https://blog.google/technology/ai/rss/"),
    Feed("simonwillison", "Simon Willison", "https://simonwillison.net/atom/everything/"),
)


def _clean(text: str | None, limit: int = 240) -> str:
    plain = WHITESPACE.sub(" ", html.unescape(TAGS.sub(" ", text or ""))).strip()
    if len(plain) <= limit:
        return plain
    head, _, _ = plain[:limit].rpartition(" ")
    return f"{head or plain[:limit]}…"


def _parse_date(raw: str | None) -> datetime | None:
    value = (raw or "").strip()
    if not value:
        return None
    try:  # Atom: ISO 8601
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:  # RSS 2.0: RFC 822
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


class FeedSource(NewsSource):
    """Lab and practitioner blogs, over RSS 2.0 or Atom.

    Both formats appear in the wild and differ in element names and date
    formats, so the parser accepts either. Adding a blog is a Feed entry, not
    another adapter.
    """

    slug = "feeds"
    label = "Blogs"
    category = AI_PRODUCTS

    def __init__(self, feeds: tuple[Feed, ...] = DEFAULT_FEEDS, per_feed: int = 6) -> None:
        self.feeds = feeds
        self.per_feed = per_feed

    async def fetch(self, client: httpx.AsyncClient, limit: int) -> list[NewsItem]:
        results = await asyncio.gather(
            *(self._fetch_feed(client, feed) for feed in self.feeds),
            return_exceptions=True,
        )

        items: list[NewsItem] = []
        failures = 0
        for result in results:
            if isinstance(result, BaseException):
                failures += 1
                continue
            items.extend(result)

        if failures == len(self.feeds):
            raise SourceError(self.slug, f"all {failures} feeds failed")

        items.sort(key=lambda item: item.published_at, reverse=True)
        return items[:limit]

    async def _fetch_feed(self, client: httpx.AsyncClient, feed: Feed) -> list[NewsItem]:
        try:
            response = await client.get(feed.url, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise SourceError(self.slug, f"{feed.slug}: {error}") from error

        return self.parse(feed, response.text)

    def parse(self, feed: Feed, payload: str) -> list[NewsItem]:
        try:
            root = ElementTree.fromstring(payload)
        except ElementTree.ParseError as error:
            raise SourceError(self.slug, f"{feed.slug}: malformed feed: {error}") from error

        entries = list(root.iter("item")) or list(root.iter(f"{ATOM}entry"))
        items: list[NewsItem] = []
        for entry in entries[: self.per_feed]:
            item = self._entry_to_item(feed, entry)
            if item is not None:
                items.append(item)
        return items

    def _entry_to_item(self, feed: Feed, entry: ElementTree.Element) -> NewsItem | None:
        is_atom = entry.tag.startswith(ATOM)
        title = _clean(entry.findtext(f"{ATOM}title" if is_atom else "title"), limit=200)
        link = self._link(entry, is_atom)
        published = _parse_date(
            entry.findtext(f"{ATOM}published") or entry.findtext(f"{ATOM}updated")
            if is_atom
            else entry.findtext("pubDate")
        )
        if not title or published is None:
            return None

        summary = _clean(
            entry.findtext(f"{ATOM}summary") or entry.findtext(f"{ATOM}content")
            if is_atom
            else entry.findtext("description")
        )
        identifier = link or f"{feed.slug}:{title}"

        return NewsItem(
            id=f"{feed.slug}:{identifier.rsplit('/', 1)[-1] or identifier}",
            title=title,
            summary=summary,
            source=feed.label,
            published_at=published,
            category=classify(title, summary, default=self.category),
            url=link or None,
        )

    @staticmethod
    def _link(entry: ElementTree.Element, is_atom: bool) -> str:
        if not is_atom:
            return (entry.findtext("link") or "").strip()
        for link in entry.iter(f"{ATOM}link"):
            if link.get("rel", "alternate") == "alternate" and link.get("href"):
                return link.get("href", "").strip()
        return ""
