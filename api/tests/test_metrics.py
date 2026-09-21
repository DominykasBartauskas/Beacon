from datetime import UTC, datetime, timedelta

from beacon_api.metrics import summarise
from beacon_api.models import NewsItem

NOW = datetime(2026, 9, 21, 12, tzinfo=UTC)


def _item(source: str, category: str, hours_ago: float) -> NewsItem:
    return NewsItem(
        id=f"{source}:{hours_ago}",
        title="t",
        summary="s",
        source=source,
        published_at=NOW - timedelta(hours=hours_ago),
        category=category,
    )


def test_an_empty_feed_reports_zeroes_rather_than_sample_numbers() -> None:
    metrics = summarise([], now=NOW)

    assert [metric.value for metric in metrics] == ["0", "0", "0"]
    assert metrics[0].label == "Stories today"


def test_counts_describe_the_loaded_feed() -> None:
    items = [
        _item("arXiv", "AI Research", 1),
        _item("Hacker News", "Software Development", 3),
        _item("Hacker News", "Software Development", 5),
        _item("GitHub", "Tools & Platforms", 30),  # outside the 24 hour window
    ]

    stories, sources, topics = summarise(items, now=NOW)

    assert stories.value == "3"
    assert stories.change == "4 in the feed"
    assert sources.value == "3"
    assert topics.value == "3"


def test_the_newest_source_and_leading_topic_are_named() -> None:
    items = [
        _item("arXiv", "AI Research", 9),
        _item("OpenAI", "AI Products & Applications", 1),
        _item("Hacker News", "Software Development", 4),
        _item("Hacker News", "Software Development", 6),
    ]

    _, sources, topics = summarise(items, now=NOW)

    assert sources.change == "Newest from OpenAI"
    assert topics.change == "2 in Software Development"
