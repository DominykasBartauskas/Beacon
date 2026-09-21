from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "beacon-api"


class NewsItem(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    published_at: datetime
    category: str
    url: str | None = None


class NewsListResponse(BaseModel):
    items: list[NewsItem]
    total: int


class DashboardMetric(BaseModel):
    label: str
    value: str
    change: str | None = None


class DashboardResponse(BaseModel):
    headline: str
    updated_at: datetime
    metrics: list[DashboardMetric]
    featured_news: list[NewsItem] = Field(default_factory=list)
