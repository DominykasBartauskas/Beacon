from datetime import datetime
from typing import Any

import httpx

from ..categories import AI_PRODUCTS, classify
from ..models import NewsItem
from .base import NewsSource, SourceError

SEARCH_URL = "https://api.x.com/2/tweets/search/recent"
POST_URL = "https://x.com/i/web/status/"
DEFAULT_QUERY = "(LLM OR \"AI model\" OR inference OR agents) -is:retweet -is:reply lang:en"
DEFAULT_MIN_LIKES = 250
# The API caps recent search at 100 per page and rejects anything under 10.
MAX_RESULTS = 100
MIN_RESULTS = 10


class XSource(NewsSource):
    """Posts from X, for accounts and topics worth watching.

    Requires a bearer token and stays disabled without one. There is no free
    path to this data: the public search page renders client side and contains
    no posts, the v2 API answers 401 unauthenticated, and scraping the internal
    endpoints breaks X's terms. So the adapter is configuration-gated rather
    than clever, and the feed simply carries on without it.
    """

    slug = "x"
    label = "X"
    category = AI_PRODUCTS

    def __init__(
        self,
        bearer_token: str = "",
        query: str = DEFAULT_QUERY,
        min_likes: int = DEFAULT_MIN_LIKES,
    ) -> None:
        self.bearer_token = bearer_token
        self.query = query
        self.min_likes = min_likes

    @property
    def enabled(self) -> bool:
        return bool(self.bearer_token)

    async def fetch(self, client: httpx.AsyncClient, limit: int) -> list[NewsItem]:
        if not self.enabled:
            return []

        params = {
            "query": self.query,
            "max_results": str(max(MIN_RESULTS, min(limit, MAX_RESULTS))),
            "tweet.fields": "created_at,public_metrics,author_id,note_tweet",
            "expansions": "author_id",
            "user.fields": "username,name",
        }
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        try:
            response = await client.get(SEARCH_URL, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise SourceError(self.slug, str(error)) from error
        except ValueError as error:
            raise SourceError(self.slug, f"malformed response: {error}") from error

        return self.parse(payload)

    def parse(self, payload: Any) -> list[NewsItem]:
        if not isinstance(payload, dict):
            raise SourceError(self.slug, "expected an object")
        posts = payload.get("data")
        if posts is None:
            return []
        if not isinstance(posts, list):
            raise SourceError(self.slug, "data was not a list")

        authors = self._authors(payload)
        items: list[NewsItem] = []
        for post in posts:
            item = self._post_to_item(post, authors)
            if item is not None:
                items.append(item)
        return items

    @staticmethod
    def _authors(payload: dict[str, Any]) -> dict[str, str]:
        users = (payload.get("includes") or {}).get("users") or []
        return {
            str(user.get("id")): str(user.get("username") or user.get("name") or "")
            for user in users
            if isinstance(user, dict) and user.get("id")
        }

    def _post_to_item(self, post: Any, authors: dict[str, str]) -> NewsItem | None:
        if not isinstance(post, dict):
            return None

        post_id = str(post.get("id") or "").strip()
        text = " ".join(str(post.get("text") or "").split())
        published = self._published(post.get("created_at"))
        if not post_id or not text or published is None:
            return None

        metrics = post.get("public_metrics") or {}
        likes = int(metrics.get("like_count") or 0)
        if likes < self.min_likes:
            return None

        author = authors.get(str(post.get("author_id") or ""), "")
        title = text if len(text) <= 120 else f"{text[:117].rstrip()}…"
        byline = f"@{author}" if author else "X"

        return NewsItem(
            id=f"{self.slug}:{post_id}",
            title=title,
            summary=f"{byline} · {likes:,} likes, {int(metrics.get('retweet_count') or 0):,} reposts.",
            source=self.label,
            published_at=published,
            category=classify(text, default=self.category),
            url=f"{POST_URL}{post_id}",
        )

    @staticmethod
    def _published(raw: Any) -> datetime | None:
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
