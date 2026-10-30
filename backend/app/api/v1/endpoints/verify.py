"""
TruthLens - Verification API Endpoints
POST /api/v1/verify                 - Submit article text/headline/URL for evidence-based verification
POST /api/v1/verify/guest-session   - Issue server-managed cryptographic guest credentials
GET  /api/v1/verify/{id}/status     - Poll job state machine and progress percentage
GET  /api/v1/verify/{id}            - Retrieve complete verified report with citations and audit trail
POST /api/v1/verify/{id}/retry      - Retry failed or interrupted verification job
POST /api/v1/verify/{id}/cancel     - Cancel an in-progress verification job
DELETE /api/v1/verify/{id}          - Delete a verification report
GET  /api/v1/verify                 - List past verification jobs scoped to user or guest session
POST /api/v1/verify/claim-guest-reports - Claim guest reports with cryptographic token validation
"""
from datetime import datetime, timedelta, timezone
import json
import logging
from typing import List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.verification import VerificationClaimRecord, VerificationJob
from app.schemas.verification import VerificationReport
from app.schemas.verification_api import (
    ClaimGuestReportsRequest,
    ClaimGuestReportsResponse,
    GuestSessionResponse,
    VerificationHistoryItem,
    VerificationJobStatusResponse,
    VerificationSubmitRequest,
)
from app.services.auth_service import get_current_user, get_optional_current_user
from app.services.extractor import extract_article_from_url, ExtractionError
from app.services.guest_session_service import guest_session_service
from app.services.verification_orchestrator import verification_orchestrator

logger = logging.getLogger("truthlens.verify_api")
router = APIRouter()

MAX_INPUT_CHARACTERS = 15000


def check_job_authorization(
    job: VerificationJob,
    current_user: Optional[User],
    guest_session_id: Optional[str]
) -> None:
    """
    Enforces strict ownership checks on verification jobs.
    - Authenticated jobs are accessible ONLY by their owning user ID.
    - Guest jobs are accessible ONLY by the matching guest session ID.
    - Never exposes authenticated data or allows unauthenticated takeover.
    """
    if job.user_id is not None:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authentication required to access this verification report."
            )
        if current_user.id != job.user_id and not getattr(current_user, "is_superuser", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access another user's verification report."
            )
    else:
        # Guest job
        if not guest_session_id or job.guest_session_id != guest_session_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this guest session report."
            )


@router.post("/guest-session", response_model=GuestSessionResponse)
def create_guest_session(db: Session = Depends(get_db)):
    """
    Issues a new cryptographically secure guest verification session.
    Provides session_id (public) and claim_token (private secret required for claiming).
    """
    session, claim_token = guest_session_service.create_session(db)
    return GuestSessionResponse(
        guest_session_id=session.id,
        claim_token=claim_token,
        expires_at=session.expires_at.isoformat()
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def submit_verification_job(
    request: VerificationSubmitRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    x_guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID")
):
    """
    Initiates asynchronous evidence-based verification for a news headline, text, or URL.
    Returns HTTP 202 Accepted with job status endpoint for real-time polling.
    Enforces input length bounds, server-side cryptographic guest sessions, and rate limits.
    """
    article_text = (request.text or "").strip()
    headline = (request.headline or "").strip()
    source_url = None

    # Resolve or create guest session
    guest_session_id = None
    if not current_user:
        candidate_guest_id = (x_guest_session_id or request.guest_session_id)
        if candidate_guest_id and candidate_guest_id.strip():
            # Validate server-issued guest session (rejects arbitrary/guessed IDs)
            session = guest_session_service.validate_session(db, candidate_guest_id.strip())
            guest_session_id = session.id
        else:
            # Automatically provision a new cryptographic guest session
            session, claim_token = guest_session_service.create_session(db)
            guest_session_id = session.id
            response.headers["X-Guest-Session-ID"] = guest_session_id
            response.headers["X-Guest-Claim-Token"] = claim_token

        # Check rate limits
        guest_session_service.record_request_and_check_rate_limit(db, session)

    # If URL provided, securely extract text with SSRF protections
    if request.url and request.url.strip():
        source_url = request.url.strip()
        try:
            extracted = extract_article_from_url(source_url)
            if not article_text:
                article_text = extracted.get("text", "")
            if not headline:
                headline = extracted.get("title", "")
        except ExtractionError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract content from URL: {str(e)}"
            )

    if not article_text and not headline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification requires news text, headline, or valid URL."
        )

    # Enforce input size limit
    if len(article_text) > MAX_INPUT_CHARACTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article text exceeds maximum allowed size of {MAX_INPUT_CHARACTERS} characters."
        )

    # Create verification job record
    job_id = f"job_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc)
    job = VerificationJob(
        id=job_id,
        user_id=current_user.id if current_user else None,
        guest_session_id=guest_session_id,
        original_text=article_text or headline,
        headline=headline or None,
        source_url=source_url,
        language=(request.language or "en").strip().lower() if request.language != "auto" else "en",
        status="QUEUED",
        current_step="Verification job registered and queued",
        progress_percent=0,
        created_at=now,
        updated_at=now
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch background orchestrator
    background_tasks.add_task(verification_orchestrator.process_job, job_id)

    return {
        "job_id": job.id,
        "status": job.status,
        "current_step": job.current_step,
        "progress_percent": job.progress_percent,
        "status_url": f"/api/v1/verify/{job.id}/status",
        "report_url": f"/api/v1/verify/{job.id}"
    }


@router.get("/{job_id}/status", response_model=VerificationJobStatusResponse)
def get_verification_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    x_guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID")
):
    """
    Returns the real-time state machine transition status and progress percentage.
    Protected by strict ownership authorization checks.
    """
    job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification job not found."
        )

    check_job_authorization(job, current_user, x_guest_session_id)

    # Compute elapsed seconds
    now = datetime.now(timezone.utc)
    created = job.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    elapsed_seconds = max(0, int((now - created).total_seconds()))

    return VerificationJobStatusResponse(
        job_id=job.id,
        status=job.status,
        current_step=job.current_step,
        progress_percent=job.progress_percent,
        elapsed_seconds=elapsed_seconds,
        error_message=job.error_message,
        overall_verdict=job.overall_verdict,
        overall_confidence=job.overall_confidence,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
        has_report=bool(job.report_json),
        is_guest_session=job.user_id is None
    )


@router.get("/{job_id}", response_model=VerificationReport)
def get_verification_report(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    x_guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID")
):
    """
    Retrieves the complete verification report, claim evaluations, and cited evidence.
    Protected by strict ownership authorization checks.
    """
    job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification job not found."
        )

    check_job_authorization(job, current_user, x_guest_session_id)

    if job.status != "COMPLETED" or not job.report_json:
        if job.status == "FAILED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Verification job failed: {job.error_message or 'Internal execution error'}"
            )
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Verification report is still being generated. Current step: {job.current_step}"
        )

    try:
        report_data = json.loads(job.report_json)
        return VerificationReport(**report_data)
    except Exception as e:
        logger.error(f"Error parsing report_json for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deserialize verification report."
        )


@router.post("/{job_id}/retry")
def retry_verification_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    x_guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID")
):
    """
    Retries a failed or cancelled verification job without creating duplicate records.
    Protected by strict ownership authorization checks.
    """
    job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification job not found."
        )

    check_job_authorization(job, current_user, x_guest_session_id)

    if job.status not in ("FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry a job in status '{job.status}'. Only FAILED or CANCELLED jobs can be retried."
        )

    # Clean intermediate claim records from failed run
    db.query(VerificationClaimRecord).filter(VerificationClaimRecord.job_id == job_id).delete()

    # Reset state to QUEUED
    now = datetime.now(timezone.utc)
    job.status = "QUEUED"
    job.current_step = "Verification job queued for retry"
    job.progress_percent = 0
    job.error_message = None
    job.updated_at = now
    db.commit()

    background_tasks.add_task(verification_orchestrator.process_job, job_id)

    return {
        "job_id": job.id,
        "status": job.status,
        "message": "Verification job re-queued successfully."
    }


@router.post("/{job_id}/cancel")
def cancel_verification_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    x_guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID")
):
    """
    Cancels an active or pending verification job in flight.
    Protected by strict ownership authorization checks.
    """
    job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification job not found."
        )

    check_job_authorization(job, current_user, x_guest_session_id)

    if job.status in ("COMPLETED", "FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in terminal status '{job.status}'."
        )

    verification_orchestrator.cancel_job(job_id, db=db)
    job.status = "CANCELLED"
    job.current_step = "Verification cancelled by user"
    job.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "job_id": job.id,
        "status": "CANCELLED",
        "message": "Verification job cancelled successfully."
    }


@router.delete("/{job_id}")
def delete_verification_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    x_guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID")
):
    """
    Deletes a verification job and all its associated claims and report records.
    Protected by strict ownership authorization checks.
    """
    job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification job not found."
        )

    check_job_authorization(job, current_user, x_guest_session_id)

    db.delete(job)
    db.commit()

    return {
        "message": f"Verification report {job_id} deleted successfully.",
        "deleted": True
    }


@router.get("", response_model=List[VerificationHistoryItem])
def list_verification_history(
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    x_guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID")
):
    """
    Lists past verification jobs strictly scoped to the authenticated user ID
    or to the active guest session. Never leaks cross-user or public reports.
    """
    if current_user:
        query = db.query(VerificationJob).filter(VerificationJob.user_id == current_user.id)
    elif x_guest_session_id and x_guest_session_id.strip():
        # Validate guest session exists and is unexpired
        try:
            session = guest_session_service.validate_session(db, x_guest_session_id.strip())
            query = db.query(VerificationJob).filter(
                VerificationJob.guest_session_id == session.id,
                VerificationJob.user_id.is_(None)
            )
        except HTTPException:
            return []
    else:
        return []

    # Optional verdict filtering
    if verdict and verdict.strip() and verdict.upper() != "ALL":
        query = query.filter(VerificationJob.overall_verdict == verdict.strip().upper())

    # Optional search filtering
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (VerificationJob.headline.ilike(term)) | (VerificationJob.original_text.ilike(term))
        )

    jobs = query.order_by(VerificationJob.created_at.desc()).limit(limit).all()

    items = []
    for j in jobs:
        claims_count = 0
        sup_count = 0
        contra_count = 0

        # Extract counts from report_json if present
        if j.report_json:
            try:
                rep = json.loads(j.report_json)
                claims_count = rep.get("claims_total", 0)
                for cr in rep.get("claim_results", []):
                    sup_count += cr.get("supporting_evidence_count", 0)
                    contra_count += cr.get("contradicting_evidence_count", 0)
            except Exception:
                pass

        items.append(
            VerificationHistoryItem(
                job_id=j.id,
                headline=j.headline or (j.original_text[:60] + "..."),
                status=j.status,
                overall_verdict=j.overall_verdict,
                overall_confidence=j.overall_confidence,
                language=j.language,
                claims_count=claims_count,
                supporting_sources_count=sup_count,
                contradicting_sources_count=contra_count,
                created_at=j.created_at.isoformat()
            )
        )

    return items


@router.post("/claim-guest-reports", response_model=ClaimGuestReportsResponse)
def claim_guest_reports(
    req: ClaimGuestReportsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Securely claims guest-session reports and attaches them to the authenticated user ID.
    Validates the private claim_token secret against stored cryptographic hash.
    Prevents guessing, replay attacks, and unauthorized session takeover.
    """
    claimed = guest_session_service.claim_session_reports(
        db=db,
        session_id=req.guest_session_id,
        claim_token=req.claim_token,
        user_id=current_user.id
    )

    return ClaimGuestReportsResponse(
        claimed_count=claimed,
        message=f"Successfully transferred {claimed} verification report(s) to your account."
    )
