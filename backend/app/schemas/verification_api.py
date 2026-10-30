"""
TruthLens - Verification API Schemas
Defines request and response schemas for initiating, polling, and reviewing
evidence-based news verification jobs, guest sessions, and history.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.verification import VerificationReport


class GuestSessionResponse(BaseModel):
    """Credentials issued when initiating a guest session."""
    guest_session_id: str = Field(..., description="Public guest session identifier")
    claim_token: str = Field(..., description="Private secret required to claim or transfer reports")
    expires_at: str = Field(..., description="ISO timestamp when the session expires")


class VerificationSubmitRequest(BaseModel):
    """Payload to initiate news verification."""
    text: Optional[str] = Field(default=None, description="News body text or social claim")
    headline: Optional[str] = Field(default=None, description="News headline or title")
    url: Optional[str] = Field(default=None, description="News article URL to extract and verify")
    language: Optional[str] = Field(default=None, description="Target language ('en', 'hi', or auto)")
    guest_session_id: Optional[str] = Field(default=None, description="Server-issued guest session ID")


class VerificationJobStatusResponse(BaseModel):
    """Job status polling response."""
    job_id: str = Field(..., description="Unique verification job ID")
    status: str = Field(..., description="Current job status (QUEUED, EXTRACTING, etc.)")
    current_step: str = Field(..., description="Human-readable description of active pipeline stage")
    progress_percent: int = Field(..., description="Estimated progress 0-100")
    elapsed_seconds: Optional[int] = Field(default=0, description="Elapsed runtime in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    overall_verdict: Optional[str] = Field(default=None, description="Synthesized verdict if completed")
    overall_confidence: Optional[float] = Field(default=None, description="Evidence consistency / corroboration score")
    created_at: str = Field(..., description="Job submission timestamp")
    updated_at: str = Field(..., description="Last state transition timestamp")
    has_report: bool = Field(default=False, description="Whether full report is ready")
    is_guest_session: bool = Field(default=False, description="Whether job is attached to a temporary guest session")


class VerificationHistoryItem(BaseModel):
    """Summary item for verification history lists."""
    job_id: str
    headline: Optional[str]
    status: str
    overall_verdict: Optional[str]
    overall_confidence: Optional[float]
    language: str
    claims_count: int = 0
    supporting_sources_count: int = 0
    contradicting_sources_count: int = 0
    created_at: str


class VerificationHistoryResponse(BaseModel):
    """Paginated verification history response."""
    items: List[VerificationHistoryItem]
    total: int
    page: int
    limit: int


class ClaimGuestReportsRequest(BaseModel):
    """Request to claim guest session reports upon account registration or login."""
    guest_session_id: str = Field(..., description="Server-issued guest session ID")
    claim_token: str = Field(..., description="Private secret required to authenticate and claim reports")


class ClaimGuestReportsResponse(BaseModel):
    """Result of claiming guest session reports."""
    claimed_count: int
    message: str
