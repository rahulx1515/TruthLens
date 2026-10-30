"""
TruthLens - Cryptographic Guest Session Security Service
Manages server-issued guest credentials with high entropy, server-side validation,
expiry enforcement, and cryptographic protection against session takeover, replay,
and guessing attacks.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import secrets
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.verification import GuestSession, VerificationJob

logger = logging.getLogger("truthlens.guest_security")

GUEST_SESSION_TTL_HOURS = 24
GUEST_HOURLY_RATE_LIMIT = 5


def hash_claim_secret(secret: str) -> str:
    """Computes SHA-256 digest of private claim secret."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class GuestSessionService:
    """
    Manages cryptographic lifecycle of guest verification sessions.
    - Generates 192-bit session IDs and 256-bit private claim tokens.
    - Enforces server-side database validation and expiration.
    - Prevents guessing, replay, and unauthorized account claiming.
    """

    def create_session(
        self,
        db: Session,
        ttl_hours: int = GUEST_SESSION_TTL_HOURS
    ) -> Tuple[GuestSession, str]:
        """
        Creates a new server-side cryptographic guest session.
        Returns the database record and the unhashed private claim_token.
        The claim_token is ONLY provided to the creating client at creation.
        """
        # 192 bits of random entropy for public session ID
        session_id = f"gses_{secrets.token_urlsafe(24)}"
        # 256 bits of random entropy for private claim secret
        claim_secret = f"gclm_{secrets.token_urlsafe(32)}"
        claim_hash = hash_claim_secret(claim_secret)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)

        session = GuestSession(
            id=session_id,
            claim_secret_hash=claim_hash,
            created_at=now,
            expires_at=expires_at,
            is_claimed=False,
            request_count=0
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"Issued cryptographic guest session {session_id[:12]}... (expires in {ttl_hours}h)")
        return session, claim_secret

    def validate_session(self, db: Session, session_id: Optional[str]) -> GuestSession:
        """
        Validates that a client-provided guest session ID exists, is active,
        is unexpired, and has not already been claimed.
        Rejects arbitrary client-invented strings.
        """
        if not session_id or not session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing guest session credentials. A server-issued guest session is required."
            )

        clean_id = session_id.strip()
        session = db.query(GuestSession).filter(GuestSession.id == clean_id).first()

        if not session:
            logger.warning(f"Rejected unknown/guessed guest session ID: {clean_id[:16]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid guest session credentials. Session ID not recognized by server."
            )

        if session.is_claimed:
            logger.warning(f"Rejected attempt to use claimed guest session: {clean_id[:16]}...")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This guest session has already been claimed and merged into a user account."
            )

        now = datetime.now(timezone.utc)
        # Ensure timezone-aware comparison
        exp = session.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if now > exp:
            logger.warning(f"Rejected expired guest session: {clean_id[:16]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Guest session has expired. Please initiate a new guest verification session."
            )

        return session

    def record_request_and_check_rate_limit(self, db: Session, session: GuestSession) -> None:
        """
        Increments request count and validates hourly rate limits on the guest session.
        """
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_count = db.query(VerificationJob).filter(
            VerificationJob.guest_session_id == session.id,
            VerificationJob.created_at >= one_hour_ago
        ).count()

        if recent_count >= GUEST_HOURLY_RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for guest session: {session.id[:16]}...")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Guest verification rate limit exceeded ({GUEST_HOURLY_RATE_LIMIT} requests/hour). "
                    "Create a free account for unlimited news investigations."
                )
            )

        session.request_count += 1
        db.commit()

    def claim_session_reports(
        self,
        db: Session,
        session_id: str,
        claim_token: str,
        user_id: int
    ) -> int:
        """
        Transfers guest reports to the authenticated user account with strict authorization.
        Prevents unauthorized claiming by validating the private claim_token secret against
        the stored cryptographic hash using constant-time comparison.
        Prevents replay attacks by checking is_claimed.
        """
        if not session_id or not session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid guest session ID must be provided."
            )
        if not claim_token or not claim_token.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid guest claim secret token must be provided to verify ownership."
            )

        session = db.query(GuestSession).filter(GuestSession.id == session_id.strip()).first()
        if not session:
            logger.warning(f"Claim failed: Session ID {session_id.strip()[:16]}... not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest session not found or does not exist."
            )

        # Replay Attack Prevention
        if session.is_claimed:
            logger.warning(f"Claim failed: Session ID {session_id.strip()[:16]}... is already claimed.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guest session has already been claimed and transferred. Replay attempts are prohibited."
            )

        # Expiry Check
        now = datetime.now(timezone.utc)
        exp = session.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            logger.warning(f"Claim failed: Session ID {session_id.strip()[:16]}... has expired.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guest session has expired. Expired session records cannot be claimed."
            )

        # Cryptographic Token Authentication (Constant-Time Comparison)
        provided_hash = hash_claim_secret(claim_token.strip())
        if not hmac.compare_digest(provided_hash, session.claim_secret_hash):
            logger.error(
                f"SECURITY ALERT: Unauthorized claim attempt for session {session_id.strip()[:16]}... "
                f"with invalid claim token by user {user_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid guest claim token. Unauthorized attempt to claim this guest session."
            )

        # Transfer all unattached jobs to user
        eligible_jobs = db.query(VerificationJob).filter(
            VerificationJob.guest_session_id == session.id,
            VerificationJob.user_id.is_(None)
        ).all()

        claimed_count = 0
        for job in eligible_jobs:
            job.user_id = user_id
            job.guest_session_id = None
            job.updated_at = now
            claimed_count += 1

        # Mark session claimed
        session.is_claimed = True
        session.claimed_by_user_id = user_id
        session.claimed_at = now
        db.commit()

        logger.info(
            f"Successfully claimed guest session {session.id[:12]}... transferred "
            f"{claimed_count} report(s) to user {user_id}."
        )
        return claimed_count


guest_session_service = GuestSessionService()

