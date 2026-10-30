"""
TruthLens 2.0 - Claim Extraction Schemas
Defines structured schemas for extracted claims, entities, query formulations,
and claim categorization.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    """Categorization of extracted statements."""
    FACTUAL = "factual"            # Checkable factual assertion
    NUMERICAL = "numerical"        # Statistical, financial, or data claim
    QUOTE = "quote"                # Quoted speech or attribution to an individual
    OPINION = "opinion"            # Subjective opinion (excluded from verification)
    PREDICTION = "prediction"      # Future speculation (unverifiable currently)


class ExtractedClaim(BaseModel):
    """A single atomic verifiable claim extracted from an article or headline."""
    id: str = Field(..., description="Unique claim identifier")
    claim_text: str = Field(..., description="Atomic, checkable claim statement")
    claim_type: ClaimType = Field(default=ClaimType.FACTUAL, description="Classification of claim")
    entities: List[str] = Field(default_factory=list, description="Named entities (people, orgs, locations)")
    dates_or_numbers: List[str] = Field(default_factory=list, description="Specific dates, metrics, percentages")
    neutral_search_query: str = Field(..., description="Neutral query designed to retrieve factual evidence")
    counter_search_query: str = Field(..., description="Counter-hypothesis query to retrieve refutations or debunks")
    language: str = Field(default="en", description="ISO language code (en or hi)")
    is_verifiable: bool = Field(default=True, description="Whether claim can be verified empirically")


class ClaimExtractionResponse(BaseModel):
    """Response containing extracted checkable claims from submitted text or article."""
    language: str = Field(..., description="Detected primary language (en, hi)")
    is_code_mixed: bool = Field(default=False, description="Whether text is code-mixed (e.g. Hinglish)")
    original_text: str = Field(..., description="Source text analyzed")
    claims: List[ExtractedClaim] = Field(default_factory=list, description="List of checkable claims")
    total_claims: int = Field(default=0, description="Total count of verifiable claims extracted")
    discarded_opinions_count: int = Field(default=0, description="Count of subjective statements filtered out")
    processing_time_ms: float = Field(default=0.0, description="Extraction duration in milliseconds")
    extraction_method: str = Field(default="llm", description="Method used: 'llm' or 'rule_based_fallback'")
    fallback_reason: Optional[str] = Field(default=None, description="Reason if rule-based fallback was used")

