"""
TruthLens 2.0 - Search & Discovery Schemas
Defines structured schemas for multi-tier search results across SearXNG,
GDELT 2.0, and curated RSS discovery feeds.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """A single retrieved search result or discovery lead."""
    url: str = Field(..., description="Canonical target URL")
    title: str = Field(..., description="Headline or page title")
    snippet: str = Field(default="", description="Search snippet or summary")
    source_domain: str = Field(..., description="Publisher domain (e.g. reuters.com)")
    provider: str = Field(..., description="Provider source: searxng, gdelt, or rss")
    published_date: Optional[str] = Field(default=None, description="Article publication date if available")
    language: str = Field(default="en", description="Language code (en or hi)")
    score: Optional[float] = Field(default=None, description="Relevance score if returned by provider")


class SearchResponse(BaseModel):
    """Aggregate search response detailing retrieved leads and provider health."""
    query: str = Field(..., description="Search query executed")
    items: List[SearchResultItem] = Field(default_factory=list, description="Retrieved leads")
    successful_providers: List[str] = Field(default_factory=list, description="Providers that succeeded")
    failed_providers: List[str] = Field(default_factory=list, description="Providers that failed or were unreachable")
    total_results: int = Field(default=0, description="Total unique results collected")

