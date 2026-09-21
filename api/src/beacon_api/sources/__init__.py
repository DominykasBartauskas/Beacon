from .arxiv import ArxivSource
from .base import NewsSource, SourceError
from .hackernews import HackerNewsSource


def default_sources() -> list[NewsSource]:
    """Every adapter the service polls. Add new ones here."""
    return [ArxivSource(), HackerNewsSource()]


__all__ = ["ArxivSource", "HackerNewsSource", "NewsSource", "SourceError", "default_sources"]
