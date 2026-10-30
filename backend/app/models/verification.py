"""
TruthLens 2.0 - Verification Database Models
Persists asynchronous verification jobs, intermediate state transitions,
extracted claims, evidence evaluations, search cache, and secure guest sessions.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


class VerificationJob(Base):
    """
    Tracks state machine transitions and findings for an evidence-based verification job.
    States: QUEUED -> EXTRACTING -> SEARCHING -> RETRIEVING -> VERIFYING -> GENERATING_REPORT -> COMPLETED / FAILED
    """
    __tablename__ = "verification_jobs"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    guest_session_id = Column(String(64), nullable=True, index=True)
    
    # Input content
    original_text = Column(Text, nullable=False)
    headline = Column(String(500), nullable=True)
    source_url = Column(String(1000), nullable=True)
    language = Column(String(10), nullable=False, default="en")
    is_code_mixed = Column(Boolean, default=False, nullable=False)

    # State machine tracking
    status = Column(String(50), nullable=False, default="QUEUED", index=True)
    current_step = Column(String(100), nullable=False, default="Queued for verification")
    progress_percent = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)

    # Final synthesized findings
    overall_verdict = Column(String(50), nullable=True, index=True)
    overall_confidence = Column(Float, nullable=True)
    report_json = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    claims = relationship("VerificationClaimRecord", back_populates="job", cascade="all, delete-orphan")
    user = relationship("User", foreign_keys=[user_id])


class VerificationClaimRecord(Base):
    """
    Stores individual investigated claims, passage evaluations, and verdicts.
    """
    __tablename__ = "verification_claims"

    id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("verification_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(50), default="factual", nullable=False)
    language = Column(String(10), default="en", nullable=False)

    verdict = Column(String(50), nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    supporting_sources_count = Column(Integer, default=0, nullable=False)
    contradicting_sources_count = Column(Integer, default=0, nullable=False)
    explanation = Column(Text, nullable=True)

    # Stored evaluations as JSON
    evaluations_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    job = relationship("VerificationJob", back_populates="claims")


class SearchCache(Base):
    """
    Caches external search results to minimize duplicate network queries.
    """
    __tablename__ = "search_cache"

    query_hash = Column(String(64), primary_key=True, index=True)
    query = Column(String(500), nullable=False)
    language = Column(String(10), default="en", nullable=False)
    results_json = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class GuestSession(Base):
    """
    Cryptographically secure server-managed guest session.
    Protects against session ID guessing, replay attacks, and unauthorized report claiming.
    """
    __tablename__ = "guest_sessions"

    id = Column(String(64), primary_key=True, index=True)
    claim_secret_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_claimed = Column(Boolean, default=False, nullable=False, index=True)
    claimed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    claimed_at = Column(DateTime, nullable=True)
    request_count = Column(Integer, default=0, nullable=False)

    user = relationship("User", foreign_keys=[claimed_by_user_id])
