"""
TruthLens - Dashboard Analytics API
GET /api/v1/dashboard/stats              - Legacy & combined dashboard statistics
GET /api/v1/dashboard/verification-stats - Evidence-based news verification metrics
"""
from datetime import datetime, timedelta, timezone
import json
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.verification import VerificationClaimRecord, VerificationJob
from app.schemas.dashboard import (
    DashboardStats,
    VerificationDashboardStats,
    VerificationDayTrend,
)
from app.schemas.verification_api import VerificationHistoryItem
from app.services.analysis_service import get_user_dashboard_stats
from app.services.auth_service import get_current_user

router = APIRouter()


def compute_user_verification_stats(db: Session, user: User) -> VerificationDashboardStats:
    """Computes evidence-based verification metrics from actual database records for user."""
    base_query = db.query(VerificationJob).filter(VerificationJob.user_id == user.id)
    total = base_query.count()

    supported = base_query.filter(VerificationJob.overall_verdict == "SUPPORTED").count()
    refuted = base_query.filter(VerificationJob.overall_verdict == "REFUTED").count()
    mixed = base_query.filter(VerificationJob.overall_verdict == "MIXED").count()
    unverified = base_query.filter(VerificationJob.overall_verdict == "UNVERIFIED").count()
    outdated = base_query.filter(VerificationJob.overall_verdict == "OUTDATED").count()

    sup_pct = round((supported / total * 100), 1) if total > 0 else 0.0
    ref_pct = round((refuted / total * 100), 1) if total > 0 else 0.0
    mix_pct = round((mixed / total * 100), 1) if total > 0 else 0.0
    unv_pct = round((unverified / total * 100), 1) if total > 0 else 0.0
    out_pct = round((outdated / total * 100), 1) if total > 0 else 0.0

    # Total claims investigated
    total_claims = (
        db.query(VerificationClaimRecord)
        .join(VerificationJob, VerificationClaimRecord.job_id == VerificationJob.id)
        .filter(VerificationJob.user_id == user.id)
        .count()
    )

    # Average supporting and contradicting sources
    avg_sup = (
        db.query(func.avg(VerificationClaimRecord.supporting_sources_count))
        .join(VerificationJob, VerificationClaimRecord.job_id == VerificationJob.id)
        .filter(VerificationJob.user_id == user.id)
        .scalar()
        or 0.0
    )

    avg_contra = (
        db.query(func.avg(VerificationClaimRecord.contradicting_sources_count))
        .join(VerificationJob, VerificationClaimRecord.job_id == VerificationJob.id)
        .filter(VerificationJob.user_id == user.id)
        .scalar()
        or 0.0
    )

    # Recent 5 verification reports
    recent_jobs = base_query.order_by(VerificationJob.created_at.desc()).limit(5).all()
    recent_items = []
    for j in recent_jobs:
        claims_c = 0
        sup_c = 0
        contra_c = 0
        if j.report_json:
            try:
                rep = json.loads(j.report_json)
                claims_c = rep.get("claims_total", 0)
                for cr in rep.get("claim_results", []):
                    sup_c += cr.get("supporting_evidence_count", 0)
                    contra_c += cr.get("contradicting_evidence_count", 0)
            except Exception:
                pass

        recent_items.append(
            VerificationHistoryItem(
                job_id=j.id,
                headline=j.headline or (j.original_text[:60] + "..."),
                status=j.status,
                overall_verdict=j.overall_verdict,
                overall_confidence=j.overall_confidence,
                language=j.language,
                claims_count=claims_c,
                supporting_sources_count=sup_c,
                contradicting_sources_count=contra_c,
                created_at=j.created_at.isoformat()
            )
        )

    # Daily trend (last 7 days)
    now = datetime.now(timezone.utc)
    daily_trend = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_query = base_query.filter(
            VerificationJob.created_at >= day_start,
            VerificationJob.created_at < day_end
        )
        d_sup = day_query.filter(VerificationJob.overall_verdict == "SUPPORTED").count()
        d_ref = day_query.filter(VerificationJob.overall_verdict == "REFUTED").count()
        d_mix = day_query.filter(VerificationJob.overall_verdict == "MIXED").count()
        d_unv = day_query.filter(VerificationJob.overall_verdict == "UNVERIFIED").count()
        d_out = day_query.filter(VerificationJob.overall_verdict == "OUTDATED").count()

        daily_trend.append(
            VerificationDayTrend(
                date=day_start.strftime("%b %d"),
                supported=d_sup,
                refuted=d_ref,
                mixed=d_mix,
                unverified=d_unv,
                outdated=d_out,
                total=d_sup + d_ref + d_mix + d_unv + d_out
            )
        )

    return VerificationDashboardStats(
        total_verifications=total,
        supported_count=supported,
        refuted_count=refuted,
        mixed_count=mixed,
        unverified_count=unverified,
        outdated_count=outdated,
        supported_percentage=sup_pct,
        refuted_percentage=ref_pct,
        mixed_percentage=mix_pct,
        unverified_percentage=unv_pct,
        outdated_percentage=out_pct,
        total_claims_investigated=total_claims,
        avg_supporting_sources=round(float(avg_sup), 2),
        avg_contradicting_sources=round(float(avg_contra), 2),
        recent_verifications=recent_items,
        daily_trend=daily_trend
    )


@router.get("/verification-stats", response_model=VerificationDashboardStats)
def get_user_verification_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes evidence-based news verification metrics for the authenticated user.
    """
    return compute_user_verification_stats(db=db, user=current_user)


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Combined analytics endpoint: returns both legacy ML stats and verification metrics.
    """
    stats = get_user_dashboard_stats(db=db, user=current_user)
    stats.verification_stats = compute_user_verification_stats(db=db, user=current_user)
    return stats
