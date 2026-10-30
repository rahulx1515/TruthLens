"""
TruthLens 2.0 - Verification & Verdict Schemas
Defines structured schemas for Natural Language Inference (NLI) evaluations,
claim-level verdicts, evidence audit trails, and final comprehensive reports.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class NLILabel(str, Enum):
    """Natural Language Inference relationship between evidence passage and claim."""
    ENTAILMENT = "entailment"          # Passage strictly implies or confirms claim
    CONTRADICTION = "contradiction"    # Passage refutes or directly opposes claim
    NEUTRAL = "neutral"                # Passage mentions related topic but neither confirms nor refutes


class FinalVerdict(str, Enum):
    """Transparent verdict categories required by TruthLens 2.0 specification."""
    SUPPORTED = "SUPPORTED"            # Strong independent evidence supports claim
    REFUTED = "REFUTED"                # Credible evidence contradicts claim
    MIXED = "MIXED"                    # Partially true, exaggerated, or cherry-picked
    UNVERIFIED = "UNVERIFIED"          # Insufficient credible evidence found (never assume fake without proof)
    OUTDATED = "OUTDATED"              # Historically accurate event presented misleadingly as current news


class NLIPassageEvaluation(BaseModel):
    """Detailed NLI inference results for an individual evidence passage against a claim."""
    passage_id: str = Field(..., description="Unique passage ID")
    article_url: str = Field(..., description="Canonical source URL")
    article_title: str = Field(default="", description="Article title")
    source_domain: str = Field(..., description="Publisher domain")
    publisher_name: str = Field(..., description="Publisher name")
    quoted_passage: str = Field(..., description="Exact quoted passage text from source")
    published_date: Optional[str] = Field(default=None, description="Original publication date")
    retrieved_at: str = Field(..., description="ISO 8601 retrieval timestamp")
    nli_label: NLILabel = Field(..., description="Winning NLI relationship label")
    entailment_prob: float = Field(default=0.0, description="NLI entailment probability")
    contradiction_prob: float = Field(default=0.0, description="NLI contradiction probability")
    neutral_prob: float = Field(default=0.0, description="NLI neutral probability")
    inference_method: str = Field(default="neural", description="Inference method: 'neural' or 'heuristic_fallback'")
    relevance_score: float = Field(default=0.0, description="BM25/semantic relevance score between passage and claim")
    exact_quotation_verified: bool = Field(default=True, description="Whether quotation exists verbatim in original source text")
    source_type: str = Field(default="secondary", description="Source classification: 'primary', 'secondary', or 'other'")
    relation_explanation: str = Field(default="", description="Explanation of how the passage relates to the claim")
    is_syndicated: bool = Field(default=False, description="Whether this is a syndicated wire copy")
    cluster_id: Optional[str] = Field(default=None, description="Syndication cluster ID")


class ClaimVerificationResult(BaseModel):
    """Complete verification evaluation for an individual claim."""
    claim_id: str = Field(..., description="Claim ID")
    claim_text: str = Field(..., description="Atomic claim statement")
    claim_type: str = Field(default="factual", description="Type of claim")
    language: str = Field(default="en", description="Claim language")
    verdict: FinalVerdict = Field(..., description="Claim-level verdict")
    confidence: float = Field(default=0.0, description="Confidence score between 0.0 and 1.0")
    supporting_evidence_count: int = Field(default=0, description="Count of distinct independent supporting sources")
    contradicting_evidence_count: int = Field(default=0, description="Count of distinct independent contradicting sources")
    evaluations: List[NLIPassageEvaluation] = Field(default_factory=list, description="Passage-level NLI evaluations")
    explanation: str = Field(default="", description="Detailed human-readable reasoning")
    why_verdict: Optional[str] = Field(default=None, description="Concise explanation in plain language")
    corroboration_score: Optional[float] = Field(default=None, description="Measured corroboration level")
    limitations: Optional[str] = Field(default=None, description="What could not be independently verified")


class VerificationReport(BaseModel):
    """Final comprehensive verification report for submitted content."""
    verification_id: str = Field(..., description="Unique report ID")
    original_title: Optional[str] = Field(default=None, description="Submitted article headline if provided")
    original_content: str = Field(..., description="Full original submitted text")
    detected_language: str = Field(default="en", description="Detected language code (en or hi)")
    is_code_mixed: bool = Field(default=False, description="Whether text is code-mixed (Hinglish)")
    overall_verdict: FinalVerdict = Field(..., description="Overall synthesized verdict")
    overall_confidence: float = Field(default=0.0, description="Overall confidence score")
    executive_summary: str = Field(..., description="Transparent synthesized summary of findings")
    why_this_verdict: Optional[str] = Field(default=None, description="Prominent explanation of why the article received this verdict")
    limitations_and_uncertainty: Optional[str] = Field(default=None, description="Known limitations, unverified elements, or evidence gaps")
    extraction_method: Optional[str] = Field(default="llm", description="Method used for claim extraction ('llm' or 'rule_based_fallback')")
    nli_inference_method: Optional[str] = Field(default="neural", description="Method used for NLI verification ('neural' or 'heuristic_fallback')")
    claims_total: int = Field(default=0, description="Total claims investigated")
    claims_supported: int = Field(default=0, description="Number of supported claims")
    claims_refuted: int = Field(default=0, description="Number of refuted claims")
    claims_unverified: int = Field(default=0, description="Number of unverified claims")
    claims_outdated: int = Field(default=0, description="Number of outdated claims")
    claim_results: List[ClaimVerificationResult] = Field(default_factory=list, description="Per-claim findings")
    search_providers_used: List[str] = Field(default_factory=list, description="Providers that yielded results")
    created_at: str = Field(..., description="Report creation timestamp")

