from .arxiv import ArxivSource
from .base import NewsSource, SourceError
from .feeds import Feed, FeedSource
from .github import GitHubReleasesSource
from .hackernews import HackerNewsSource
from .huggingface import HuggingFaceSource


def default_sources(github_token: str = "") -> list[NewsSource]:
    """Every adapter the service polls. Add new ones here."""
    return [
        ArxivSource(),
        HackerNewsSource(),
        HuggingFaceSource(),
        GitHubReleasesSource(token=github_token),
        FeedSource(),
    ]


__all__ = [
    "ArxivSource",
    "Feed",
    "FeedSource",
    "GitHubReleasesSource",
    "HackerNewsSource",
    "HuggingFaceSource",
    "NewsSource",
    "SourceError",
    "default_sources",
]
