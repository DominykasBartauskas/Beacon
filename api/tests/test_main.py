from fastapi.testclient import TestClient

from beacon_api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "beacon-api"}


def test_news_respects_limit() -> None:
    response = client.get("/api/v1/news?limit=2")

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] >= 2


def test_dashboard_has_featured_news() -> None:
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.json()["headline"]
    assert len(response.json()["featured_news"]) == 3
