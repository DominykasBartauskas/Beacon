import asyncio
import re
from datetime import datetime
from typing import Any

import httpx

from ..categories import TOOLS_PLATFORMS, classify
from ..models import NewsItem
from .base import NewsSource, SourceError

API_ROOT = "https://api.github.com/repos/"
# One request per repository per refresh, against 60/hour unauthenticated.
# The service cache keeps that well inside the limit; a token raises it to 5000.
DEFAULT_REPOS = (
    "vllm-project/vllm",
    "huggingface/transformers",
    "langchain-ai/langchain",
    "ggml-org/llama.cpp",
    "pytorch/pytorch",
    "openai/openai-python",
    "anthropics/anthropic-sdk-python",
    "modelcontextprotocol/servers",
)
RELEASES_PER_REPO = 2

MARKDOWN_NOISE = (
    (re.compile(r"```.*?```", re.S), " "),          # fenced code
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), " "),     # images
    (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),  # links keep their text
    (re.compile(r"<[^>]+>"), " "),                  # inline html
    (re.compile(r"[#*_`>|-]+"), " "),               # heading and emphasis marks
    (re.compile(r"\s+"), " "),
)


def _plain(body: str | None, limit: int = 220) -> str:
    text = body or ""
    for pattern, replacement in MARKDOWN_NOISE:
        text = pattern.sub(replacement, text)
    text = text.strip()
    if len(text) <= limit:
        return text
    head, _, _ = text[:limit].rpartition(" ")
    return f"{head or text[:limit]}…"


class GitHubReleasesSource(NewsSource):
    """Releases from a watchlist of AI and infrastructure repositories."""

    slug = "github"
    label = "GitHub"
    category = TOOLS_PLATFORMS

    def __init__(self, repos: tuple[str, ...] = DEFAULT_REPOS, token: str = "") -> None:
        self.repos = repos
        self.token = token

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def fetch(self, client: httpx.AsyncClient, limit: int) -> list[NewsItem]:
        results = await asyncio.gather(
            *(self._fetch_repo(client, repo) for repo in self.repos),
            return_exceptions=True,
        )

        items: list[NewsItem] = []
        failures = 0
        for result in results:
            if isinstance(result, BaseException):
                failures += 1
                continue
            items.extend(result)

        # One repository being renamed or archived should not kill the source.
        if failures == len(self.repos):
            raise SourceError(self.slug, f"all {failures} repositories failed")

        items.sort(key=lambda item: item.published_at, reverse=True)
        return items[:limit]

    async def _fetch_repo(self, client: httpx.AsyncClient, repo: str) -> list[NewsItem]:
        url = f"{API_ROOT}{repo}/releases"
        try:
            response = await client.get(
                url, params={"per_page": str(RELEASES_PER_REPO)}, headers=self.headers
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise SourceError(self.slug, f"{repo}: {error}") from error
        except ValueError as error:
            raise SourceError(self.slug, f"{repo}: malformed response: {error}") from error

        return self.parse(repo, payload)

    def parse(self, repo: str, payload: Any) -> list[NewsItem]:
        if not isinstance(payload, list):
            raise SourceError(self.slug, f"{repo}: expected a list of releases")

        items: list[NewsItem] = []
        for release in payload:
            item = self._release_to_item(repo, release)
            if item is not None:
                items.append(item)
        return items

    def _release_to_item(self, repo: str, release: Any) -> NewsItem | None:
        if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
            return None

        tag = str(release.get("tag_name") or "").strip()
        published = self._published(release.get("published_at"))
        if not tag or published is None:
            return None

        project = repo.split("/", 1)[-1]
        name = str(release.get("name") or "").strip()
        title = f"{project} {tag} released"
        summary = _plain(release.get("body")) or f"{project} published release {tag}."
        if name and name != tag:
            summary = f"{name}. {summary}"

        return NewsItem(
            id=f"{self.slug}:{repo}:{tag}",
            title=title,
            summary=summary,
            source=self.label,
            published_at=published,
            category=classify(title, summary, default=self.category),
            url=str(release.get("html_url") or "").strip() or f"https://github.com/{repo}/releases",
        )

    @staticmethod
    def _published(raw: Any) -> datetime | None:
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
