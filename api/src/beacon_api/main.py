from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .data import METRICS, NOW
from .models import DashboardResponse, HealthResponse, NewsListResponse
from .news import NewsService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    timeout = httpx.Timeout(settings.news_request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        app.state.news_service = NewsService(
            client,
            enabled=settings.live_news_enabled,
            cache_ttl_seconds=settings.news_cache_ttl_seconds,
            fetch_limit=settings.news_fetch_limit,
        )
        yield


def get_news_service() -> NewsService:
    return app.state.news_service


settings = get_settings()
USER_AGENT = "beacon-api/0.1 (+https://github.com/DominykasBartauskas/Beacon)"
app = FastAPI(
    title="Beacon API",
    version="0.1.0",
    description="A small, typed API for the Beacon local-news dashboard.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse()


@app.get("/api/v1/news", response_model=NewsListResponse, tags=["news"])
async def list_news(
    limit: int = Query(default=10, ge=1, le=50),
    news: NewsService = Depends(get_news_service),
) -> NewsListResponse:
    items = await news.items()
    return NewsListResponse(items=items[:limit], total=len(items))


@app.get("/api/v1/dashboard", response_model=DashboardResponse, tags=["dashboard"])
async def dashboard(news: NewsService = Depends(get_news_service)) -> DashboardResponse:
    items = await news.items()
    return DashboardResponse(
        headline="Your local signal, at a glance.",
        updated_at=NOW,
        metrics=METRICS,
        featured_news=items[:3],
    )
