"""
Dashboard Analytics API
GET /api/v1/dashboard/stats
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardStats
from app.services.analysis_service import get_user_dashboard_stats
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes dashboard analytics from real backend database records:
    total count, fake vs authentic breakdown, percentages, confidence, and daily volume.
    """
    return get_user_dashboard_stats(db=db, user=current_user)

