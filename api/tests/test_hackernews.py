from datetime import UTC, datetime

import httpx
import pytest

from beacon_api.categories import SAFETY_SECURITY, SOFTWARE_DEVELOPMENT
from beacon_api.sources import HackerNewsSource
from beacon_api.sources.base import SourceError

PAYLOAD = {
    "hits": [
        {
            "objectID": "44567857",
            "title": "A jailbreak of a production coding assistant",
            "url": "https://example.com/post",
            "points": 1773,
            "num_comments": 1628,
            "created_at": "2026-05-04T09:12:00Z",
        },
        {
            "objectID": "44567999",
            "title": "Ask HN: how do you review generated code?",
            "url": "",
            "points": 210,
            "num_comments": 96,
            "created_at": "2026-05-03T11:00:00Z",
        },
        {"objectID": "", "title": "no id", "created_at": "2026-05-02T11:00:00Z"},
        {"objectID": "44568111", "title": "no timestamp"},
    ]
}


def test_parses_hits() -> None:
    items = HackerNewsSource().parse(PAYLOAD)

    assert len(items) == 2
    first = items[0]
    assert first.id == "hackernews:44567857"
    assert first.source == "Hacker News"
    assert first.url == "https://example.com/post"
    assert first.summary == "1773 points and 1628 comments on Hacker News."
    assert first.published_at == datetime(2026, 5, 4, 9, 12, tzinfo=UTC)


def test_categories_come_from_the_title() -> None:
    items = HackerNewsSource().parse(PAYLOAD)

    assert items[0].category == SAFETY_SECURITY
    assert items[1].category == SOFTWARE_DEVELOPMENT


def test_stories_without_a_link_fall_back_to_the_discussion() -> None:
    items = HackerNewsSource().parse(PAYLOAD)

    assert items[1].url == "https://news.ycombinator.com/item?id=44567999"


def test_rejects_a_response_without_hits() -> None:
    with pytest.raises(SourceError):
        HackerNewsSource().parse({"nope": []})


@pytest.mark.anyio
async def test_fetch_applies_the_points_threshold() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json=PAYLOAD)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await HackerNewsSource(min_points=250).fetch(client, limit=7)

    assert len(items) == 2
    assert seen["numericFilters"] == "points>=250"
    assert seen["tags"] == "story"
    assert seen["optionalWords"] == seen["query"]
    assert seen["hitsPerPage"] == "7"


@pytest.mark.anyio
async def test_fetch_wraps_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SourceError):
            await HackerNewsSource().fetch(client, limit=5)


@pytest.mark.anyio
async def test_fetch_rejects_non_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>nope</html>")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SourceError):
            await HackerNewsSource().fetch(client, limit=5)
