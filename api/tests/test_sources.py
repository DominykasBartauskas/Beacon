from datetime import UTC, datetime

import httpx
import pytest

from beacon_api.models import NewsItem
from beacon_api.news import NewsService, dedupe
from beacon_api.sources import ArxivSource
from beacon_api.sources import arxiv
from beacon_api.sources.base import NewsSource, SourceError

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2505.01234v1</id>
    <title>A study of
      retrieval under ambiguity</title>
    <summary>  We look at how systems behave when the evidence is incomplete.  </summary>
    <published>2026-05-04T09:12:00Z</published>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2505.05678v2</id>
    <title>Scaling evaluation loops</title>
    <summary>A lighter review checkpoint for fast-moving prompts.</summary>
    <published>2026-05-03T17:40:00Z</published>
  </entry>
  <entry>
    <id></id>
    <title>Missing identifier, should be skipped</title>
    <summary>No id.</summary>
    <published>2026-05-02T10:00:00Z</published>
  </entry>
</feed>
"""


def _item(item_id: str, title: str, url: str | None, minutes: int) -> NewsItem:
    return NewsItem(
        id=item_id,
        title=title,
        summary="",
        source="test",
        published_at=datetime(2026, 5, 4, 9, minutes, tzinfo=UTC),
        category="AI Research",
        url=url,
    )


class StubSource(NewsSource):
    slug = "stub"
    label = "Stub"
    category = "AI Research"

    def __init__(self, items: list[NewsItem] | None = None, error: Exception | None = None) -> None:
        self.items = items or []
        self.error = error
        self.calls = 0

    async def fetch(self, client: httpx.AsyncClient, limit: int) -> list[NewsItem]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.items[:limit]


def test_arxiv_parses_entries() -> None:
    items = ArxivSource().parse(FEED)

    assert len(items) == 2
    first = items[0]
    assert first.id == "arxiv:2505.01234v1"
    assert first.title == "A study of retrieval under ambiguity"
    assert first.summary == "We look at how systems behave when the evidence is incomplete."
    assert first.source == "arXiv"
    assert first.category == "AI Research"
    assert first.url == "http://arxiv.org/abs/2505.01234v1"
    assert first.published_at == datetime(2026, 5, 4, 9, 12, tzinfo=UTC)


def test_arxiv_rejects_malformed_feed() -> None:
    with pytest.raises(SourceError):
        ArxivSource().parse("<feed><entry>")


@pytest.mark.anyio
async def test_arxiv_fetch_uses_the_atom_api() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, text=FEED)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        items = await ArxivSource().fetch(client, limit=5)

    assert len(items) == 2
    assert seen["sortBy"] == "submittedDate"
    assert seen["max_results"] == "5"
    assert "cat:cs.AI" in seen["search_query"]


@pytest.mark.anyio
async def test_arxiv_fetch_wraps_transport_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SourceError):
            await ArxivSource().fetch(client, limit=5)


@pytest.mark.anyio
async def test_arxiv_retries_when_throttled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(arxiv, "RETRY_BACKOFF_SECONDS", 0)
    statuses = [406, 406, 200]

    def handler(request: httpx.Request) -> httpx.Response:
        status = statuses.pop(0)
        return httpx.Response(status, text=FEED if status == 200 else "throttled")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        items = await ArxivSource().fetch(client, limit=5)

    assert not statuses
    assert len(items) == 2


@pytest.mark.anyio
async def test_arxiv_gives_up_after_repeated_throttling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(arxiv, "RETRY_BACKOFF_SECONDS", 0)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(406, text="throttled")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SourceError, match="throttled"):
            await ArxivSource().fetch(client, limit=5)

    assert calls == arxiv.RETRY_ATTEMPTS


@pytest.mark.anyio
async def test_arxiv_does_not_retry_other_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(arxiv, "RETRY_BACKOFF_SECONDS", 0)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(404, text="gone")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SourceError):
            await ArxivSource().fetch(client, limit=5)

    assert calls == 1


def test_dedupe_collapses_the_same_url() -> None:
    items = [
        _item("a", "First report", "https://example.com/story/", 30),
        _item("b", "First report, reposted", "http://www.example.com/story", 10),
        _item("c", "Something else", "https://example.com/other", 20),
    ]

    result = dedupe(items)

    assert [item.id for item in result] == ["c", "b"]


def test_dedupe_falls_back_to_the_title() -> None:
    items = [
        _item("a", "Same   Headline", None, 30),
        _item("b", "same headline", None, 10),
    ]

    assert len(dedupe(items)) == 1


@pytest.mark.anyio
async def test_service_serves_samples_when_disabled() -> None:
    source = StubSource(items=[_item("a", "Live", "https://example.com/a", 5)])
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
        service = NewsService(client, [source], enabled=False)
        items = await service.items()

    assert source.calls == 0
    assert items == service.fallback


@pytest.mark.anyio
async def test_service_falls_back_when_every_source_fails() -> None:
    source = StubSource(error=SourceError("stub", "boom"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
        service = NewsService(client, [source])
        items = await service.items()

    assert source.calls == 1
    assert items == service.fallback


@pytest.mark.anyio
async def test_service_caches_between_calls() -> None:
    source = StubSource(items=[_item("a", "Live", "https://example.com/a", 5)])
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
        service = NewsService(client, [source])
        first = await service.items()
        second = await service.items()

    assert source.calls == 1
    assert first == second == [source.items[0]]


@pytest.mark.anyio
async def test_service_refetches_once_the_cache_expires() -> None:
    source = StubSource(items=[_item("a", "Live", "https://example.com/a", 5)])
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
        service = NewsService(client, [source], cache_ttl_seconds=0)
        await service.items()
        await service.items()

    assert source.calls == 2
