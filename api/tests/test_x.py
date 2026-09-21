from datetime import UTC, datetime

import httpx
import pytest

from beacon_api.sources import XSource, default_sources
from beacon_api.sources.base import SourceError

PAYLOAD = {
    "data": [
        {
            "id": "1900000000000000001",
            "text": "We are shipping a new inference stack today. Throughput is up 4x.",
            "created_at": "2026-09-21T09:00:00.000Z",
            "author_id": "42",
            "public_metrics": {"like_count": 3120, "retweet_count": 410},
        },
        {
            "id": "1900000000000000002",
            "text": "quiet post nobody liked",
            "created_at": "2026-09-21T08:00:00.000Z",
            "author_id": "42",
            "public_metrics": {"like_count": 3, "retweet_count": 0},
        },
    ],
    "includes": {"users": [{"id": "42", "username": "someone", "name": "Some One"}]},
}


def test_disabled_without_a_token() -> None:
    assert XSource().enabled is False
    assert XSource(bearer_token="t").enabled is True


def test_it_is_left_out_of_the_default_sources_without_a_token() -> None:
    slugs = [source.slug for source in default_sources()]
    assert "x" not in slugs

    slugs_with_token = [source.slug for source in default_sources(x_bearer_token="t")]
    assert "x" in slugs_with_token


@pytest.mark.anyio
async def test_fetch_returns_nothing_when_disabled() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("must not call the API without a token")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert await XSource().fetch(client, limit=5) == []


def test_parses_posts_and_applies_the_like_threshold() -> None:
    items = XSource(bearer_token="t").parse(PAYLOAD)

    assert len(items) == 1
    item = items[0]
    assert item.id == "x:1900000000000000001"
    assert item.summary == "@someone · 3,120 likes, 410 reposts."
    assert item.url == "https://x.com/i/web/status/1900000000000000001"
    assert item.published_at == datetime(2026, 9, 21, 9, tzinfo=UTC)


def test_long_posts_are_truncated_for_the_title() -> None:
    payload = {
        "data": [{
            "id": "1", "text": "word " * 60, "created_at": "2026-09-21T09:00:00.000Z",
            "public_metrics": {"like_count": 900},
        }]
    }

    title = XSource(bearer_token="t").parse(payload)[0].title
    assert len(title) <= 120
    assert title.endswith("…")


def test_an_empty_result_set_is_not_an_error() -> None:
    assert XSource(bearer_token="t").parse({"meta": {"result_count": 0}}) == []


def test_rejects_a_malformed_payload() -> None:
    with pytest.raises(SourceError):
        XSource(bearer_token="t").parse({"data": "nope"})


@pytest.mark.anyio
async def test_fetch_sends_the_bearer_token() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.headers)
        seen.update(request.url.params)
        return httpx.Response(200, json=PAYLOAD)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await XSource(bearer_token="secret").fetch(client, limit=5)

    assert seen["authorization"] == "Bearer secret"
    assert seen["max_results"] == "10"   # the API rejects anything under ten
    assert len(items) == 1


@pytest.mark.anyio
async def test_unauthorized_is_reported_as_a_source_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"title": "Unauthorized"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SourceError):
            await XSource(bearer_token="stale").fetch(client, limit=5)
