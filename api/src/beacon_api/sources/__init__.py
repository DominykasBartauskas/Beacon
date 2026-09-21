from .arxiv import ArxivSource
from .base import NewsSource, SourceError
from .feeds import Feed, FeedSource
from .github import GitHubReleasesSource
from .hackernews import HackerNewsSource
from .huggingface import HuggingFaceSource
from .x import XSource


def default_sources(github_token: str = "", x_bearer_token: str = "") -> list[NewsSource]:
    """Every adapter the service polls. Add new ones here.

    X is omitted without a token: it is the one source with no free tier, and
    an adapter that can only fail is worse than an absent one.
    """
    sources: list[NewsSource] = [
        ArxivSource(),
        HackerNewsSource(),
        HuggingFaceSource(),
        GitHubReleasesSource(token=github_token),
        FeedSource(),
    ]
    if x_bearer_token:
        sources.append(XSource(bearer_token=x_bearer_token))
    return sources


__all__ = [
    "ArxivSource",
    "Feed",
    "FeedSource",
    "GitHubReleasesSource",
    "HackerNewsSource",
    "HuggingFaceSource",
    "NewsSource",
    "SourceError",
    "XSource",
    "default_sources",
]
