"""
TruthLens 2.0 - Evidence & Passage Schemas
Defines schemas for extracted evidence passages, publisher attribution,
syndication clustering, and exact quotation tracking.
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class EvidencePassage(BaseModel):
    """An exact textual passage extracted from a retrieved news article."""
    passage_id: str = Field(..., description="Unique passage identifier")
    article_url: str = Field(..., description="Canonical source URL")
    article_title: str = Field(default="", description="Article title")
    canonical_domain: str = Field(..., description="Domain of publisher (e.g. pib.gov.in)")
    publisher_name: str = Field(..., description="Publisher name")
    passage_text: str = Field(..., description="Exact quoted passage text (verbatim from source)")
    word_count: int = Field(default=0, description="Word count of passage")
    published_date: Optional[str] = Field(default=None, description="Original publication date")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 retrieval timestamp"
    )
    relevance_score: float = Field(default=0.0, description="BM25 or dense retrieval score")
    
    # Syndication and independence tracking
    cluster_id: Optional[str] = Field(default=None, description="Syndication cluster ID if syndicated")
    is_syndicated_copy: bool = Field(default=False, description="True if identical/wire copy of another article")
    primary_source_url: Optional[str] = Field(default=None, description="URL of primary source if syndicated")


class EvidenceCollectionResponse(BaseModel):
    """Aggregate retrieved evidence passages for a specific claim."""
    claim_id: str = Field(..., description="Claim being investigated")
    claim_text: str = Field(..., description="Original claim text")
    language: str = Field(default="en", description="Language of claim")
    passages: List[EvidencePassage] = Field(default_factory=list, description="Top ranked evidence passages")
    total_passages_found: int = Field(default=0, description="Total candidate passages before filtering")
    independent_sources_count: int = Field(default=0, description="Number of distinct non-syndicated publishers")
    syndicated_copies_count: int = Field(default=0, description="Number of duplicate/syndicated passages filtered")

