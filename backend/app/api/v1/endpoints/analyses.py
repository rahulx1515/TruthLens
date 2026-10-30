"""
Analysis History Endpoints
GET /api/v1/analyses
GET /api/v1/analyses/{id}
DELETE /api/v1/analyses/{id}
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.analysis import AnalysisListResponse, AnalysisResponse
from app.services.analysis_service import delete_analysis_by_id, get_analysis_by_id, list_analyses
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("", response_model=AnalysisListResponse)
def get_analyses(
    search: Optional[str] = Query(None, description="Search by title or domain"),
    filter: Optional[str] = Query(None, description="Filter by 'FAKE' or 'REAL'"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches paginated list of analysis records for the authenticated user."""
    return list_analyses(
        db=db,
        user=current_user,
        search=search,
        prediction_filter=filter,
        page=page,
        limit=limit
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches a specific analysis report by ID with user ownership check."""
    return get_analysis_by_id(db=db, analysis_id=analysis_id, user=current_user)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes an analysis report owned by the authenticated user."""
    delete_analysis_by_id(db=db, analysis_id=analysis_id, user=current_user)
    return None

