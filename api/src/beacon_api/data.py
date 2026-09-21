from datetime import UTC, datetime, timedelta

from .models import NewsItem

NOW = datetime.now(UTC)

NEWS = [
    NewsItem(
        id="city-garden",
        title="City gardens are making room for a new growing season",
        summary="Community plots are opening registration with workshops for first-time growers.",
        source="Beacon Local",
        published_at=NOW - timedelta(minutes=38),
        category="Community",
        url="https://example.com/city-gardens",
    ),
    NewsItem(
        id="river-path",
        title="Riverside path reopens after a spring refresh",
        summary="The popular walking route now has improved lighting and additional seating.",
        source="Daily Signal",
        published_at=NOW - timedelta(hours=2),
        category="Local",
        url="https://example.com/river-path",
    ),
    NewsItem(
        id="makers-market",
        title="Makers market puts local studios in the spotlight",
        summary="More than forty independent makers will gather downtown this weekend.",
        source="The Ledger",
        published_at=NOW - timedelta(hours=5),
        category="Culture",
        url="https://example.com/makers-market",
    ),
    NewsItem(
        id="transit-update",
        title="Transit agency adds late-evening service",
        summary="A pilot schedule will connect major neighborhoods later on weekdays.",
        source="Beacon Local",
        published_at=NOW - timedelta(hours=8),
        category="Transit",
        url="https://example.com/transit-update",
    ),
]
