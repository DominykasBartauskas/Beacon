from datetime import UTC, datetime

import httpx
import pytest

from beacon_api.categories import TOOLS_PLATFORMS
from beacon_api.sources import GitHubReleasesSource
from beacon_api.sources.base import SourceError

RELEASES = [
    {
        "tag_name": "v0.29.0",
        "name": "Model Runner V2",
        "published_at": "2026-09-09T08:54:49Z",
        "html_url": "https://github.com/vllm-project/vllm/releases/tag/v0.29.0",
        "draft": False,
        "prerelease": False,
        "body": "# v0.29.0\n\n## Highlights\n\n594 commits from 277 contributors. See [the docs](https://example.com) and `pip install vllm`.\n\n```python\nprint('x')\n```",
    },
    {"tag_name": "v0.30.0rc1", "published_at": "2026-09-10T08:00:00Z", "prerelease": True},
    {"tag_name": "v0.28.0-draft", "published_at": "2026-09-08T08:00:00Z", "draft": True},
    {"tag_name": "", "published_at": "2026-09-07T08:00:00Z"},
]


def test_parses_releases_and_skips_drafts_and_prereleases() -> None:
    items = GitHubReleasesSource().parse("vllm-project/vllm", RELEASES)

    assert len(items) == 1
    item = items[0]
    assert item.id == "github:vllm-project/vllm:v0.29.0"
    assert item.title == "vllm v0.29.0 released"
    assert item.source == "GitHub"
    assert item.published_at == datetime(2026, 9, 9, 8, 54, 49, tzinfo=UTC)


def test_release_notes_are_flattened_to_plain_text() -> None:
    summary = GitHubReleasesSource().parse("vllm-project/vllm", RELEASES)[0].summary

    assert summary.startswith("Model Runner V2.")
    assert "594 commits from 277 contributors" in summary
    assert "the docs" in summary          # link text survives
    assert "https://example.com" not in summary   # link target does not
    assert "```" not in summary and "#" not in summary
    assert "print(" not in summary        # fenced code is dropped


def test_a_release_lands_in_tools_and_platforms() -> None:
    assert GitHubReleasesSource().parse("vllm-project/vllm", RELEASES)[0].category == TOOLS_PLATFORMS


def test_rejects_a_non_list_response() -> None:
    with pytest.raises(SourceError):
        GitHubReleasesSource().parse("a/b", {"message": "Not Found"})


@pytest.mark.anyio
async def test_fetch_merges_repositories_newest_first() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        repo = str(request.url).split("/repos/", 1)[1].rsplit("/releases", 1)[0]
        stamp = {"a/one": "2026-09-01T00:00:00Z", "a/two": "2026-09-05T00:00:00Z"}[repo]
        return httpx.Response(200, json=[{
            "tag_name": "v1", "published_at": stamp, "draft": False, "prerelease": False,
            "html_url": f"https://github.com/{repo}/releases/tag/v1", "body": "notes",
        }])

    source = GitHubReleasesSource(repos=("a/one", "a/two"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await source.fetch(client, limit=10)

    assert [item.id for item in items] == ["github:a/two:v1", "github:a/one:v1"]


@pytest.mark.anyio
async def test_one_failing_repository_does_not_sink_the_source() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "gone" in str(request.url):
            return httpx.Response(404, json={"message": "Not Found"})
        return httpx.Response(200, json=[{
            "tag_name": "v1", "published_at": "2026-09-01T00:00:00Z",
            "draft": False, "prerelease": False, "body": "notes",
        }])

    source = GitHubReleasesSource(repos=("a/gone", "a/alive"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await source.fetch(client, limit=10)

    assert [item.id for item in items] == ["github:a/alive:v1"]


@pytest.mark.anyio
async def test_every_repository_failing_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    source = GitHubReleasesSource(repos=("a/one", "a/two"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SourceError, match="all 2 repositories failed"):
            await source.fetch(client, limit=10)


@pytest.mark.anyio
async def test_a_token_is_sent_when_configured() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.headers)
        return httpx.Response(200, json=[])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await GitHubReleasesSource(repos=("a/one",), token="secret").fetch(client, limit=5)

    assert seen["authorization"] == "Bearer secret"
