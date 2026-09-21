from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from beacon_api.data import NEWS
from beacon_api.main import app, get_news_service
from beacon_api.models import NewsItem


class StubNewsService:
    """Stands in for `NewsService` so the endpoint tests never touch the network."""

    def __init__(self, items: list[NewsItem]) -> None:
        self._items = items

    async def items(self) -> list[NewsItem]:
        return self._items


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_news_service] = lambda: StubNewsService(list(NEWS))
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "beacon-api"}


def test_news_respects_limit(client: TestClient) -> None:
    response = client.get("/api/v1/news?limit=2")

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] >= 2


def test_dashboard_has_featured_news(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.json()["headline"]
    assert len(response.json()["featured_news"]) == 3


def test_news_serves_what_the_service_returns() -> None:
    live = NewsItem(
        id="arxiv:2505.01234v1",
        title="A study of retrieval under ambiguity",
        summary="We look at how systems behave when the evidence is incomplete.",
        source="arXiv",
        published_at=datetime(2026, 5, 4, 9, 12, tzinfo=UTC),
        category="AI Research",
        url="http://arxiv.org/abs/2505.01234v1",
    )
    app.dependency_overrides[get_news_service] = lambda: StubNewsService([live])

    with TestClient(app) as test_client:
        body = test_client.get("/api/v1/news").json()

    app.dependency_overrides.clear()

    assert body["total"] == 1
    assert body["items"][0]["source"] == "arXiv"
    assert body["items"][0]["category"] == "AI Research"
