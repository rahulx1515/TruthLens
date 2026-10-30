"""
TruthLens - Dashboard Analytics Schemas
Defines schemas for both evidence-based news verification statistics
and backward-compatible legacy ML analytics.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.analysis import AnalysisListItem
from app.schemas.verification_api import VerificationHistoryItem


class DayDistribution(BaseModel):
    date: str
    fake_count: int = 0
    authentic_count: int = 0
    total: int = 0


class VerificationDayTrend(BaseModel):
    date: str
    supported: int = 0
    refuted: int = 0
    mixed: int = 0
    unverified: int = 0
    outdated: int = 0
    total: int = 0


class VerificationDashboardStats(BaseModel):
    """User-scoped analytics for evidence-based verification."""
    total_verifications: int = 0
    supported_count: int = 0
    refuted_count: int = 0
    mixed_count: int = 0
    unverified_count: int = 0
    outdated_count: int = 0
    supported_percentage: float = 0.0
    refuted_percentage: float = 0.0
    mixed_percentage: float = 0.0
    unverified_percentage: float = 0.0
    outdated_percentage: float = 0.0
    total_claims_investigated: int = 0
    avg_supporting_sources: float = 0.0
    avg_contradicting_sources: float = 0.0
    recent_verifications: List[VerificationHistoryItem] = Field(default_factory=list)
    daily_trend: List[VerificationDayTrend] = Field(default_factory=list)


class DashboardStats(BaseModel):
    """Legacy dashboard stats for backward compatibility with existing tests."""
    total_analyses: int = 0
    fake_count: int = 0
    authentic_count: int = 0
    fake_percentage: float = 0.0
    authentic_percentage: float = 0.0
    average_confidence: float = 0.0
    recent_analyses: List[AnalysisListItem] = Field(default_factory=list)
    daily_trend: List[DayDistribution] = Field(default_factory=list)
    # Embedded verification metrics
    verification_stats: Optional[VerificationDashboardStats] = None
