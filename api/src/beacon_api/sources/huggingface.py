from datetime import datetime
from typing import Any

import httpx

from ..categories import MODELS_RELEASES, classify
from ..models import NewsItem
from .base import NewsSource, SourceError

MODELS_URL = "https://huggingface.co/api/models"
MODEL_PAGE = "https://huggingface.co/"
# Sorting by creation date returns empty scratch repos; trendingScore is what
# the Hub's own listing ranks by, so it carries the releases people reacted to.
DEFAULT_SORT = "trendingScore"
NOISE_TAGS = frozenset({"region:us", "region:eu"})


def _describe(model: dict[str, Any]) -> str:
    likes = int(model.get("likes") or 0)
    downloads = int(model.get("downloads") or 0)
    task = str(model.get("pipeline_tag") or "").replace("-", " ").strip()

    parts = [f"{likes:,} likes", f"{downloads:,} downloads"]
    if task:
        parts.append(task)
    tags = [
        tag for tag in (model.get("tags") or [])
        if isinstance(tag, str) and ":" not in tag and tag not in NOISE_TAGS
    ][:3]
    trailer = f" Tagged {', '.join(tags)}." if tags else ""
    return f"Trending on Hugging Face with {parts[0]} and {parts[1]}.{trailer}"


class HuggingFaceSource(NewsSource):
    """Trending model releases from the Hugging Face Hub."""

    slug = "huggingface"
    label = "Hugging Face"
    category = MODELS_RELEASES

    def __init__(self, sort: str = DEFAULT_SORT, min_likes: int = 0) -> None:
        self.sort = sort
        self.min_likes = min_likes

    async def fetch(self, client: httpx.AsyncClient, limit: int) -> list[NewsItem]:
        params = {"sort": self.sort, "direction": "-1", "limit": str(limit)}
        try:
            response = await client.get(MODELS_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise SourceError(self.slug, str(error)) from error
        except ValueError as error:
            raise SourceError(self.slug, f"malformed response: {error}") from error

        return self.parse(payload)

    def parse(self, payload: Any) -> list[NewsItem]:
        if not isinstance(payload, list):
            raise SourceError(self.slug, "expected a list of models")

        items: list[NewsItem] = []
        for model in payload:
            item = self._model_to_item(model)
            if item is not None:
                items.append(item)
        return items

    def _model_to_item(self, model: Any) -> NewsItem | None:
        if not isinstance(model, dict):
            return None

        model_id = str(model.get("id") or "").strip()
        published = self._published(model.get("createdAt"))
        if not model_id or published is None:
            return None
        if int(model.get("likes") or 0) < self.min_likes:
            return None

        title = model_id.split("/", 1)[-1] if "/" in model_id else model_id
        author = model_id.split("/", 1)[0] if "/" in model_id else self.label
        summary = _describe(model)

        return NewsItem(
            id=f"{self.slug}:{model_id}",
            title=f"{title} released by {author}",
            summary=summary,
            source=self.label,
            published_at=published,
            category=classify(title, summary, default=self.category),
            url=f"{MODEL_PAGE}{model_id}",
        )

    @staticmethod
    def _published(raw: Any) -> datetime | None:
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
