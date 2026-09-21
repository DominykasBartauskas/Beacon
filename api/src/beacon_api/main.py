from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .data import METRICS, NEWS, NOW
from .models import DashboardResponse, HealthResponse, NewsListResponse


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


settings = get_settings()
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
async def list_news(limit: int = Query(default=10, ge=1, le=50)) -> NewsListResponse:
    items = NEWS[:limit]
    return NewsListResponse(items=items, total=len(NEWS))


@app.get("/api/v1/dashboard", response_model=DashboardResponse, tags=["dashboard"])
async def dashboard() -> DashboardResponse:
    return DashboardResponse(
        headline="Your local signal, at a glance.",
        updated_at=NOW,
        metrics=METRICS,
        featured_news=NEWS[:3],
    )
