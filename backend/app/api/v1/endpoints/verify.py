"""
TruthLens 2.0 - Verification API Endpoints
POST /api/v1/verify          - Submit article text/headline/URL for evidence-based verification
GET  /api/v1/verify/{id}/status - Poll job state machine and progress percentage
GET  /api/v1/verify/{id}     - Retrieve complete verified report with citations and audit trail
POST /api/v1/verify/{id}/retry - Retry failed or interrupted verification job
GET  /api/v1/verify          - List past verification jobs
"""
from datetime import datetime, timezone
import json
import logging
from typing import List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.verification import VerificationJob
from app.schemas.verification import VerificationReport
from app.schemas.verification_api import (
    VerificationHistoryItem,
    VerificationJobStatusResponse,
    VerificationSubmitRequest,
)
from app.services.auth_service import get_optional_current_user
from app.services.extractor import extract_article_from_url, ExtractionError
from app.services.verification_orchestrator import verification_orchestrator

logger = logging.getLogger("truthlens.verify_api")
router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def submit_verification_job(
    request: VerificationSubmitRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Initiates asynchronous evidence-based verification for a news headline, text, or URL.
    Returns HTTP 202 Accepted with job status endpoint for real-time polling.
    """
    article_text = (request.text or "").strip()
    headline = (request.headline or "").strip()
    source_url = None

    # If URL provided, securely extract text
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
            detail="Either article text, headline, or a valid news URL must be provided."
        )

    job_id = f"job_{uuid.uuid4().hex[:12]}"

    # Persist initial QUEUED state
    job = VerificationJob(
        id=job_id,
        user_id=current_user.id if current_user else None,
        original_text=article_text or headline,
        headline=headline or None,
        source_url=source_url,
        language=request.language or "en",
        status="QUEUED",
        current_step="Verification job submitted and queued",
        progress_percent=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch to background task worker
    background_tasks.add_task(verification_orchestrator.process_job, job_id)

    return {
        "job_id": job_id,
        "status": "QUEUED",
        "current_step": "Verification job submitted and queued",
        "progress_percent": 0,
        "status_url": f"/api/v1/verify/{job_id}/status",
        "report_url": f"/api/v1/verify/{job_id}"
    }


@router.get("/{job_id}/status", response_model=VerificationJobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Polls the real-time state machine progress for an ongoing or completed job.
    """
    job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")

    return VerificationJobStatusResponse(
        job_id=job.id,
        status=job.status,
        current_step=job.current_step,
        progress_percent=job.progress_percent,
        error_message=job.error_message,
        overall_verdict=job.overall_verdict,
        overall_confidence=job.overall_confidence,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
        has_report=bool(job.report_json)
    )


@router.get("/{job_id}", response_model=VerificationReport)
def get_verification_report(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the complete verification report and evidence audit trail.
    """
    job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")

    if job.status == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verification job failed: {job.error_message or 'Unknown error'}"
        )

    if job.status != "COMPLETED" or not job.report_json:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Verification in progress: {job.current_step} ({job.progress_percent}%)"
        )

    try:
        report_data = json.loads(job.report_json)
        return VerificationReport(**report_data)
    except Exception as e:
        logger.error(f"Failed to parse report JSON for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving verification report payload."
        )


@router.post("/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_verification_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Retries an interrupted or failed verification job without creating duplicate records.
    """
    job = verification_orchestrator.retry_job(job_id, db)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")

    background_tasks.add_task(verification_orchestrator.process_job, job_id)

    return {
        "job_id": job.id,
        "status": job.status,
        "message": "Verification job queued for retry.",
        "status_url": f"/api/v1/verify/{job.id}/status"
    }


@router.get("", response_model=List[VerificationHistoryItem])
def list_verification_jobs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Lists recent verification jobs.
    If authenticated, returns user's jobs; otherwise returns public recent items.
    """
    query = db.query(VerificationJob)
    if current_user:
        query = query.filter(VerificationJob.user_id == current_user.id)
    
    jobs = query.order_by(VerificationJob.created_at.desc()).limit(limit).all()

    return [
        VerificationHistoryItem(
            job_id=j.id,
            headline=j.headline or (j.original_text[:60] + "..."),
            status=j.status,
            overall_verdict=j.overall_verdict,
            overall_confidence=j.overall_confidence,
            language=j.language,
            created_at=j.created_at.isoformat()
        )
        for j in jobs
    ]

