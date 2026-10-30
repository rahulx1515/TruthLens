"""
TruthLens 2.0 - Verification API Schemas
Defines request and response schemas for initiating, polling, and reviewing
evidence-based news verification jobs.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.verification import VerificationReport


class VerificationSubmitRequest(BaseModel):
    """Payload to initiate news verification."""
    text: Optional[str] = Field(default=None, description="News body text or social claim")
    headline: Optional[str] = Field(default=None, description="News headline or title")
    url: Optional[str] = Field(default=None, description="News article URL to extract and verify")
    language: Optional[str] = Field(default=None, description="Target language ('en', 'hi', or auto)")


class VerificationJobStatusResponse(BaseModel):
    """Job status polling response."""
    job_id: str = Field(..., description="Unique verification job ID")
    status: str = Field(..., description="Current job status (QUEUED, EXTRACTING, etc.)")
    current_step: str = Field(..., description="Human-readable description of active pipeline stage")
    progress_percent: int = Field(..., description="Estimated progress 0-100")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    overall_verdict: Optional[str] = Field(default=None, description="Synthesized verdict if completed")
    overall_confidence: Optional[float] = Field(default=None, description="Confidence score")
    created_at: str = Field(..., description="Job submission timestamp")
    updated_at: str = Field(..., description="Last state transition timestamp")
    has_report: bool = Field(default=False, description="Whether full report is ready")


class VerificationHistoryItem(BaseModel):
    """Summary item for verification history lists."""
    job_id: str
    headline: Optional[str]
    status: str
    overall_verdict: Optional[str]
    overall_confidence: Optional[float]
    language: str
    created_at: str

