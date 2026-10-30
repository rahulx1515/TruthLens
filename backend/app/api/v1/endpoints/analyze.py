"""
News Credibility Prediction API
POST /api/v1/analyze
"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import analyze_article
from app.services.auth_service import get_optional_current_user

router = APIRouter()


@router.post("", response_model=AnalysisResponse)
def analyze_news(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Analyzes news credibility and predicts Fake vs Authentic news.
    Accepts:
    - News headline
    - News article full body
    - Optional URL (scraped securely with SSRF prevention)
    - Optional selected model engine ('logistic_regression', 'random_forest')
    
    Returns structured prediction, calibrated confidence, processing time,
    directional feature attribution (Explainable AI), and factual limitations disclaimer.
    """
    return analyze_article(db=db, request=request, current_user=current_user)

