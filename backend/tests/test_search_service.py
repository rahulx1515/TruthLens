"""
TruthLens 2.0 - Search Infrastructure & SSRF Redirect Security Tests
Tests multi-tier search orchestration, provider fallback, URL deduplication,
and SSRF redirect revalidation security.
"""
import pytest
from app.schemas.search import SearchResponse, SearchResultItem
from app.services.extractor import ExtractionError, extract_article_from_url, validate_url_safety
from app.services.search_service import MultiTierSearchService, search_service


def test_search_service_empty_query():
    """Verify empty query returns clean empty SearchResponse."""
    resp = search_service.search("")
    assert resp.total_results == 0
    assert len(resp.items) == 0
    assert resp.successful_providers == []


def test_search_service_deduplication():
    """Verify duplicate URLs across providers are cleanly deduplicated."""
    service = MultiTierSearchService()
    
    # Mock return values with duplicates
    item1 = SearchResultItem(
        url="https://reuters.com/article/1",
        title="Title 1",
        source_domain="reuters.com",
        provider="searxng",
        language="en"
    )
    item2 = SearchResultItem(
        url="https://reuters.com/article/1",  # duplicate URL
        title="Title 1 (GDELT duplicate)",
        source_domain="reuters.com",
        provider="gdelt",
        language="en"
    )
    item3 = SearchResultItem(
        url="https://thehindu.com/article/2",
        title="Title 2",
        source_domain="thehindu.com",
        provider="rss",
        language="en"
    )

    service.searxng.search = lambda q, lang="en", max_results=8: [item1]
    service.gdelt.search = lambda q, lang="en", max_results=8: [item2]
    service.rss.search = lambda q, lang="en", max_results=6: [item3]

    resp = service.search("climate summit")
    assert resp.total_results == 2
    assert len(resp.items) == 2
    urls = [it.url for it in resp.items]
    assert urls == ["https://reuters.com/article/1", "https://thehindu.com/article/2"]
    assert "searxng" in resp.successful_providers
    assert "gdelt" in resp.successful_providers
    assert "rss" in resp.successful_providers


def test_search_provider_failure_graceful_handling():
    """Ensure failure in all search providers is reported without crashing."""
    service = MultiTierSearchService()
    service.searxng.search = lambda q, lang="en", max_results=8: []
    service.gdelt.search = lambda q, lang="en", max_results=8: []
    service.rss.search = lambda q, lang="en", max_results=6: []

    resp = service.search("unverifiable obscure assertion")
    assert resp.total_results == 0
    assert len(resp.items) == 0
    assert "searxng" in resp.failed_providers
    assert "gdelt" in resp.failed_providers
    assert "rss" in resp.failed_providers


def test_ssrf_internal_ip_rejection():
    """Verify SSRF protection strictly rejects private and loopback IPs."""
    with pytest.raises(ExtractionError, match="blocked for security|internal"):
        validate_url_safety("http://127.0.0.1:8000/secret")

    with pytest.raises(ExtractionError, match="blocked for security|internal"):
        validate_url_safety("http://localhost:3000/admin")

    with pytest.raises(ExtractionError, match="blocked for security|internal"):
        validate_url_safety("http://192.168.1.1/router-login")

    with pytest.raises(ExtractionError, match="blocked for security|internal"):
        validate_url_safety("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(ExtractionError, match="blocked for security|internal"):
        validate_url_safety("http://10.0.0.1/internal-api")


def test_ssrf_invalid_scheme_rejection():
    """Verify non-HTTP schemes are blocked."""
    with pytest.raises(ExtractionError, match="Unsupported URL scheme"):
        validate_url_safety("ftp://example.com/file.txt")

    with pytest.raises(ExtractionError, match="Unsupported URL scheme"):
        validate_url_safety("file:///etc/passwd")

