from .arxiv import ArxivSource
from .base import NewsSource, SourceError
from .hackernews import HackerNewsSource
from .huggingface import HuggingFaceSource


def default_sources() -> list[NewsSource]:
    """Every adapter the service polls. Add new ones here."""
    return [ArxivSource(), HackerNewsSource(), HuggingFaceSource()]


__all__ = [
    "ArxivSource",
    "HackerNewsSource",
    "HuggingFaceSource",
    "NewsSource",
    "SourceError",
    "default_sources",
]
