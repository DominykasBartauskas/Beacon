from datetime import datetime
from typing import Any

import httpx

from ..categories import SOFTWARE_DEVELOPMENT, classify
from ..models import NewsItem
from .base import NewsSource, SourceError

# search_by_date, not search: relevance ranking surfaces years-old threads.
SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
# Algolia ANDs query words; optionalWords is what makes them behave as OR.
DEFAULT_TERMS = "AI LLM model agents inference"
DEFAULT_MIN_POINTS = 100
ITEM_URL = "https://news.ycombinator.com/item?id="


class HackerNewsSource(NewsSource):
    """Popular Hacker News stories, via the free Algolia search API.

    Points act as the quality filter the raw feeds lack: the threshold is what
    separates a discussion worth surfacing from the rest of the firehose.
    """

    slug = "hackernews"
    label = "Hacker News"
    category = SOFTWARE_DEVELOPMENT

    def __init__(self, terms: str = DEFAULT_TERMS, min_points: int = DEFAULT_MIN_POINTS) -> None:
        self.terms = terms
        self.min_points = min_points

    async def fetch(self, client: httpx.AsyncClient, limit: int) -> list[NewsItem]:
        params = {
            "tags": "story",
            "query": self.terms,
            "optionalWords": self.terms,
            "numericFilters": f"points>={self.min_points}",
            "hitsPerPage": str(limit),
        }
        try:
            response = await client.get(SEARCH_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise SourceError(self.slug, str(error)) from error
        except ValueError as error:
            raise SourceError(self.slug, f"malformed response: {error}") from error

        return self.parse(payload)

    def parse(self, payload: Any) -> list[NewsItem]:
        if not isinstance(payload, dict) or not isinstance(payload.get("hits"), list):
            raise SourceError(self.slug, "response had no hits")

        items: list[NewsItem] = []
        for hit in payload["hits"]:
            item = self._hit_to_item(hit)
            if item is not None:
                items.append(item)
        return items

    def _hit_to_item(self, hit: Any) -> NewsItem | None:
        if not isinstance(hit, dict):
            return None

        object_id = str(hit.get("objectID") or "").strip()
        title = str(hit.get("title") or "").strip()
        published = self._published(hit.get("created_at"))
        if not object_id or not title or published is None:
            return None

        points = int(hit.get("points") or 0)
        comments = int(hit.get("num_comments") or 0)
        summary = f"{points} points and {comments} comments on Hacker News."

        return NewsItem(
            id=f"{self.slug}:{object_id}",
            title=title,
            summary=summary,
            source=self.label,
            published_at=published,
            category=classify(title, default=self.category),
            # Prefer the article itself; Ask HN and similar carry no outbound link.
            url=str(hit.get("url") or "").strip() or f"{ITEM_URL}{object_id}",
        )

    @staticmethod
    def _published(raw: Any) -> datetime | None:
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
