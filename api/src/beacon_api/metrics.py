from collections import Counter
from datetime import UTC, datetime, timedelta

from .models import DashboardMetric, NewsItem

RECENT_WINDOW = timedelta(hours=24)


def summarise(items: list[NewsItem], *, now: datetime | None = None) -> list[DashboardMetric]:
    """Describe the feed that is actually loaded.

    The dashboard used to show fixed sample numbers, which contradicted the
    feed underneath them as soon as it went live.
    """
    moment = now or datetime.now(UTC)
    if not items:
        return [
            DashboardMetric(label="Stories today", value="0", change="Nothing loaded yet"),
            DashboardMetric(label="Sources", value="0", change="No sources responded"),
            DashboardMetric(label="Topics covered", value="0", change="Waiting on the feed"),
        ]

    recent = [item for item in items if moment - item.published_at <= RECENT_WINDOW]
    sources = Counter(item.source for item in items)
    categories = Counter(item.category for item in items)
    newest = max(items, key=lambda item: item.published_at)
    leading_category, leading_count = categories.most_common(1)[0]

    return [
        DashboardMetric(
            label="Stories today",
            value=str(len(recent)),
            change=f"{len(items)} in the feed",
        ),
        DashboardMetric(
            label="Sources",
            value=str(len(sources)),
            change=f"Newest from {newest.source}",
        ),
        DashboardMetric(
            label="Topics covered",
            value=str(len(categories)),
            change=f"{leading_count} in {leading_category}",
        ),
    ]
