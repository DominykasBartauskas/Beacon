from datetime import UTC, datetime

import httpx
import pytest

from beacon_api.categories import AI_PRODUCTS, SAFETY_SECURITY
from beacon_api.sources import Feed, FeedSource
from beacon_api.sources.base import SourceError

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item>
    <title><![CDATA[Building standards for the next phase]]></title>
    <description><![CDATA[<p>An <b>alignment</b> update &amp; more.</p>]]></description>
    <link>https://example.com/news/standards</link>
    <pubDate>Mon, 21 Sep 2026 12:00:00 GMT</pubDate>
  </item>
  <item>
    <title>No timestamp</title><link>https://example.com/x</link>
  </item>
</channel></rss>
"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Quoting voxium</title>
    <link href="https://example.net/2026/Sep/20/voxium/" rel="alternate"/>
    <published>2026-09-20T21:06:43+00:00</published>
    <summary type="html">&lt;p&gt;A short note about deployment.&lt;/p&gt;</summary>
  </entry>
</feed>
"""

RSS_FEED = Feed("lab", "Lab", "https://example.com/rss")
ATOM_FEED = Feed("blog", "Blog", "https://example.net/atom")


def test_parses_rss_and_strips_markup() -> None:
    items = FeedSource().parse(RSS_FEED, RSS)

    assert len(items) == 1
    item = items[0]
    assert item.title == "Building standards for the next phase"
    assert item.summary == "An alignment update & more."
    assert item.source == "Lab"
    assert item.url == "https://example.com/news/standards"
    assert item.published_at == datetime(2026, 9, 21, 12, tzinfo=UTC)


def test_parses_atom_with_its_own_date_format() -> None:
    items = FeedSource().parse(ATOM_FEED, ATOM)

    assert len(items) == 1
    item = items[0]
    assert item.title == "Quoting voxium"
    assert item.summary == "A short note about deployment."
    assert item.url == "https://example.net/2026/Sep/20/voxium/"
    assert item.published_at == datetime(2026, 9, 20, 21, 6, 43, tzinfo=UTC)


def test_entries_are_classified_from_their_text() -> None:
    assert FeedSource().parse(RSS_FEED, RSS)[0].category == SAFETY_SECURITY
    assert FeedSource().parse(ATOM_FEED, "<rss><channel></channel></rss>") == []


def test_unclassifiable_entries_keep_the_source_category() -> None:
    feed = """<?xml version="1.0"?><rss version="2.0"><channel><item>
      <title>A quiet Tuesday</title><link>https://example.com/q</link>
      <pubDate>Mon, 21 Sep 2026 12:00:00 GMT</pubDate></item></channel></rss>"""

    assert FeedSource().parse(RSS_FEED, feed)[0].category == AI_PRODUCTS


def test_per_feed_limit_is_respected() -> None:
    entries = "".join(
        f"<item><title>Post {n}</title><link>https://example.com/{n}</link>"
        f"<pubDate>Mon, 21 Sep 2026 12:00:00 GMT</pubDate></item>"
        for n in range(10)
    )
    feed = f'<?xml version="1.0"?><rss version="2.0"><channel>{entries}</channel></rss>'

    assert len(FeedSource(per_feed=3).parse(RSS_FEED, feed)) == 3


def test_rejects_malformed_xml() -> None:
    with pytest.raises(SourceError):
        FeedSource().parse(RSS_FEED, "<rss><channel>")


@pytest.mark.anyio
async def test_fetch_merges_feeds_newest_first() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=RSS if "rss" in str(request.url) else ATOM)

    source = FeedSource(feeds=(RSS_FEED, ATOM_FEED))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await source.fetch(client, limit=10)

    assert [item.source for item in items] == ["Lab", "Blog"]


@pytest.mark.anyio
async def test_one_dead_feed_does_not_sink_the_source() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "rss" in str(request.url):
            return httpx.Response(404, text="gone")
        return httpx.Response(200, text=ATOM)

    source = FeedSource(feeds=(RSS_FEED, ATOM_FEED))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await source.fetch(client, limit=10)

    assert [item.source for item in items] == ["Blog"]


@pytest.mark.anyio
async def test_every_feed_failing_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="down")

    source = FeedSource(feeds=(RSS_FEED, ATOM_FEED))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SourceError, match="all 2 feeds failed"):
            await source.fetch(client, limit=10)
