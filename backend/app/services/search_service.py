"""
TruthLens 2.0 - Multi-Tier Live Search Infrastructure
Provides evidence discovery across SearXNG, GDELT 2.0 DOC API, and curated RSS news feeds.
Ensures zero hard dependency on Docker, graceful fallback when providers fail,
and strict reporting of which providers returned results.
"""
import logging
from typing import Dict, List, Optional, Set
from urllib.parse import quote_plus, urlparse
import feedparser
import httpx

from app.core.config import settings
from app.schemas.search import SearchResponse, SearchResultItem

logger = logging.getLogger("truthlens.search")


class SearchProviderError(Exception):
    """Exception raised by individual search providers."""
    pass


class SearXNGClient:
    """Client for configurable SearXNG instances."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.SEARXNG_URL).rstrip("/")
        # Optional public fallbacks if local endpoint is not configured/running
        self.public_fallbacks = [
            "https://searx.be",
            "https://search.ononoki.org",
            "https://searxng.site"
        ]

    def search(self, query: str, lang: str = "en", max_results: int = 8) -> List[SearchResultItem]:
        """Query SearXNG endpoint with graceful fallback."""
        candidates = [self.base_url] + self.public_fallbacks
        last_error = None

        for endpoint in candidates:
            if not endpoint:
                continue
            try:
                searx_lang = "hi" if lang == "hi" else "en"
                url = f"{endpoint}/search?q={quote_plus(query)}&format=json&language={searx_lang}"
                with httpx.Client(timeout=8.0) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        results = []
                        for item in data.get("results", [])[:max_results]:
                            target_url = item.get("url", "")
                            if not target_url or not target_url.startswith("http"):
                                continue
                            domain = urlparse(target_url).netloc
                            results.append(
                                SearchResultItem(
                                    url=target_url,
                                    title=item.get("title", ""),
                                    snippet=item.get("content", ""),
                                    source_domain=domain,
                                    provider="searxng",
                                    published_date=item.get("publishedDate"),
                                    language=lang,
                                    score=item.get("score")
                                )
                            )
                        if results:
                            return results
            except Exception as e:
                last_error = e
                continue

        logger.info(f"SearXNG unavailable on all candidate endpoints: {last_error}")
        return []


class GDELTClient:
    """
    Client for GDELT 2.0 DOC API.
    Treats GDELT results strictly as discovery metadata for original article URLs.
    """

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    def search(self, query: str, lang: str = "en", max_results: int = 8) -> List[SearchResultItem]:
        """Search GDELT 2.0 DOC API for news article leads."""
        if not settings.GDELT_ENABLED:
            return []

        try:
            # Query GDELT article list mode
            clean_query = query.replace('"', '').strip()[:80]
            url = f"{self.BASE_URL}?query={quote_plus(clean_query)}&mode=artlist&maxrecords={max_results}&format=json"
            
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except Exception:
                        return []
                    
                    results = []
                    for art in data.get("articles", []):
                        target_url = art.get("url", "")
                        if not target_url or not target_url.startswith("http"):
                            continue
                        domain = art.get("domain", "") or urlparse(target_url).netloc
                        results.append(
                            SearchResultItem(
                                url=target_url,
                                title=art.get("title", ""),
                                snippet="",  # GDELT artlist does not provide text, only metadata
                                source_domain=domain,
                                provider="gdelt",
                                published_date=art.get("seendate"),
                                language=art.get("language", lang)
                            )
                        )
                    return results
        except Exception as e:
            logger.info(f"GDELT query failed: {e}")
            return []
        return []


class RSSDiscoveryClient:
    """
    Curated RSS feed discovery provider for Indian and International media.
    Matches claim terms against recent feed entries.
    """

    FEEDS_EN = [
        ("pib.gov.in", "https://pib.gov.in/RssMain.aspx?ModId=6"),
        ("thehindu.com", "https://www.thehindu.com/news/national/feeder/default.rss"),
        ("bbc.com", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("ndtv.com", "https://feeds.feedburner.com/ndtvnews-top-stories"),
    ]

    FEEDS_HI = [
        ("bbc.com/hindi", "https://feeds.bbci.co.uk/hindi/rss.xml"),
        ("ndtv.in", "https://feeds.feedburner.com/ndtvkhabar-latest"),
        ("aajtak.in", "https://www.aajtak.in/rssfeeds/?id=home"),
    ]

    def search(self, query: str, lang: str = "en", max_results: int = 6) -> List[SearchResultItem]:
        """Search curated RSS feeds matching query keywords."""
        if not settings.RSS_ENABLED:
            return []

        feeds = self.FEEDS_HI if lang == "hi" else self.FEEDS_EN
        query_terms = {t.lower() for t in query.split() if len(t) > 2}
        results = []

        for domain, feed_url in feeds:
            try:
                parsed = feedparser.parse(feed_url)
                for entry in parsed.entries[:20]:
                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "")
                    combined_text = f"{title} {summary}".lower()

                    # Match keyword overlap
                    overlap = sum(1 for term in query_terms if term in combined_text)
                    if overlap >= 2 or (len(query_terms) <= 2 and overlap >= 1):
                        results.append(
                            SearchResultItem(
                                url=getattr(entry, "link", ""),
                                title=title,
                                snippet=summary[:200] if summary else "",
                                source_domain=domain,
                                provider="rss",
                                published_date=getattr(entry, "published", None),
                                language=lang
                            )
                        )
                    if len(results) >= max_results:
                        return results
            except Exception as e:
                logger.info(f"RSS parse failed for {domain}: {e}")
                continue

        return results


class MultiTierSearchService:
    """
    Coordinates multi-tier search across SearXNG, GDELT, and RSS feeds.
    Provides transparent reporting of successful and failed search providers.
    """

    def __init__(self):
        self.searxng = SearXNGClient()
        self.gdelt = GDELTClient()
        self.rss = RSSDiscoveryClient()

    def search(self, query: str, lang: str = "en", max_results: int = 10) -> SearchResponse:
        """
        Executes search across all available providers with fallback and deduplication.
        """
        if not query or not query.strip():
            return SearchResponse(query="", items=[], successful_providers=[], failed_providers=[], total_results=0)

        successful_providers: List[str] = []
        failed_providers: List[str] = []
        all_results: List[SearchResultItem] = []
        seen_urls: Set[str] = set()

        # 1. Primary: SearXNG
        searx_items = self.searxng.search(query, lang=lang)
        if searx_items:
            successful_providers.append("searxng")
            for item in searx_items:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    all_results.append(item)
        else:
            failed_providers.append("searxng")

        # 2. Secondary Discovery: GDELT
        gdelt_items = self.gdelt.search(query, lang=lang)
        if gdelt_items:
            successful_providers.append("gdelt")
            for item in gdelt_items:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    all_results.append(item)
        else:
            failed_providers.append("gdelt")

        # 3. Secondary Discovery: RSS Feeds
        rss_items = self.rss.search(query, lang=lang)
        if rss_items:
            successful_providers.append("rss")
            for item in rss_items:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    all_results.append(item)
        else:
            failed_providers.append("rss")

        return SearchResponse(
            query=query,
            items=all_results[:max_results],
            successful_providers=successful_providers,
            failed_providers=failed_providers,
            total_results=len(all_results[:max_results])
        )


# Global singleton instance
search_service = MultiTierSearchService()

