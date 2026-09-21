from datetime import UTC, datetime

import httpx
import pytest

from beacon_api.categories import MODELS_RELEASES
from beacon_api.sources import HuggingFaceSource
from beacon_api.sources.base import SourceError

PAYLOAD = [
    {
        "id": "Qwen/Qwen-Image-2.1",
        "likes": 1337,
        "downloads": 250000,
        "createdAt": "2026-09-14T08:00:00.000Z",
        "pipeline_tag": "text-to-image",
        "tags": ["diffusers", "safetensors", "region:us", "license:apache-2.0", "image"],
    },
    {"id": "solo-model", "likes": 4, "downloads": 10, "createdAt": "2026-09-13T08:00:00.000Z"},
    {"id": "", "likes": 9, "createdAt": "2026-09-12T08:00:00.000Z"},
    {"id": "no/timestamp", "likes": 9},
]


def test_parses_models() -> None:
    items = HuggingFaceSource().parse(PAYLOAD)

    assert len(items) == 2
    first = items[0]
    assert first.id == "huggingface:Qwen/Qwen-Image-2.1"
    assert first.title == "Qwen-Image-2.1 released by Qwen"
    assert first.url == "https://huggingface.co/Qwen/Qwen-Image-2.1"
    assert first.source == "Hugging Face"
    assert first.published_at == datetime(2026, 9, 14, 8, tzinfo=UTC)


def test_summary_carries_the_signal_and_drops_noise_tags() -> None:
    summary = HuggingFaceSource().parse(PAYLOAD)[0].summary

    assert "1,337 likes" in summary
    assert "250,000 downloads" in summary
    assert "region:us" not in summary
    assert "license:apache-2.0" not in summary
    assert "diffusers" in summary


def test_a_release_lands_in_models_and_releases() -> None:
    assert HuggingFaceSource().parse(PAYLOAD)[0].category == MODELS_RELEASES


def test_min_likes_filters_scratch_repos() -> None:
    items = HuggingFaceSource(min_likes=100).parse(PAYLOAD)

    assert [item.id for item in items] == ["huggingface:Qwen/Qwen-Image-2.1"]


def test_rejects_a_non_list_response() -> None:
    with pytest.raises(SourceError):
        HuggingFaceSource().parse({"models": []})


@pytest.mark.anyio
async def test_fetch_requests_trending_models() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json=PAYLOAD)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await HuggingFaceSource().fetch(client, limit=12)

    assert len(items) == 2
    assert seen["sort"] == "trendingScore"
    assert seen["limit"] == "12"


@pytest.mark.anyio
async def test_fetch_wraps_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="down")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SourceError):
            await HuggingFaceSource().fetch(client, limit=5)
