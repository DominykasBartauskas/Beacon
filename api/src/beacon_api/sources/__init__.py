from .arxiv import ArxivSource
from .base import NewsSource, SourceError


def default_sources() -> list[NewsSource]:
    """Every adapter the service polls. Add new ones here."""
    return [ArxivSource()]


__all__ = ["ArxivSource", "NewsSource", "SourceError", "default_sources"]
