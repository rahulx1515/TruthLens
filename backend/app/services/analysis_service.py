"""
TruthLens - Analysis Management Service
Coordinates URL extraction, ML prediction, persistence, search, and dashboard aggregation.
"""
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ml.predictor import get_predictor
from app.models.analysis import Analysis
from app.models.article import Article
from app.models.user import User
from app.schemas.analysis import AnalysisListItem, AnalysisListResponse, AnalysisRequest, AnalysisResponse
from app.schemas.dashboard import DashboardStats, DayDistribution
from app.services.extractor import ExtractionError, extract_article_from_url


def analyze_article(
    db: Session,
    request: AnalysisRequest,
    current_user: Optional[User] = None
) -> AnalysisResponse:
    """
    Core analysis pipeline:
    1. Extracts content from URL if provided
    2. Validates content presence
    3. Runs ML inference with feature attribution
    4. Persists records to PostgreSQL/SQLite
    5. Returns unified response
    """
    article_title = request.title or ""
    article_text = request.text or ""
    article_url = request.url
    article_domain = None
    author = None
    published_date = None

    # Step 1: URL Extraction if specified
    if article_url:
        try:
            extracted = extract_article_from_url(str(article_url))
            article_domain = extracted.get("domain")
            author = extracted.get("author")
            published_date = extracted.get("published_date")
            
            # If user provided no custom title/text, adopt extracted content
            if not article_title:
                article_title = extracted.get("title", "")
            if not article_text:
                article_text = extracted.get("text", "")
        except ExtractionError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL Extraction Failed: {str(e)}"
            )

    # Step 2: Validation
    if not article_title.strip() and not article_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either headline or article text must be provided."
        )

    # Step 3: ML Inference
    predictor = get_predictor()
    ml_result = predictor.predict(
        title=article_title,
        text=article_text,
        model_name=request.model_name
    )

    # Step 4: Persistence
    article = Article(
        title=article_title,
        content=article_text,
        url=str(article_url) if article_url else None,
        domain=article_domain,
        author=author,
        published_date=published_date
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    # If an anonymous user submits, bind to a system demo user if no current_user
    user_id = current_user.id if current_user else None
    if user_id is None:
        # Check or create default demo user for tracking
        demo_user = db.query(User).filter(User.email == "guest@truthlens.ai").first()
        if not demo_user:
            demo_user = User(
                email="guest@truthlens.ai",
                hashed_password="guest_demo_user_unusable_hash",
                full_name="Guest User",
                is_active=True
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        user_id = demo_user.id

    analysis = Analysis(
        user_id=user_id,
        article_id=article.id,
        prediction=ml_result["prediction"],
        label=ml_result["label"],
        confidence=ml_result["confidence"],
        prob_fake=ml_result["probabilities"]["fake"],
        prob_real=ml_result["probabilities"]["real"],
        model_name=ml_result["model_name"],
        model_version=ml_result["model_version"],
        processing_time_ms=ml_result["processing_time_ms"],
        explanation_json=json.dumps(ml_result["explanation"]),
        created_at=datetime.now(timezone.utc)
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return AnalysisResponse(
        id=analysis.id,
        prediction=analysis.prediction,
        label=analysis.label,
        confidence=analysis.confidence,
        probabilities={
            "fake": analysis.prob_fake,
            "real": analysis.prob_real
        },
        model_name=analysis.model_name,
        model_version=analysis.model_version,
        processing_time_ms=analysis.processing_time_ms,
        explanation=ml_result["explanation"],
        disclaimer=ml_result["disclaimer"],
        article=article,
        created_at=analysis.created_at
    )


def list_analyses(
    db: Session,
    user: User,
    search: Optional[str] = None,
    prediction_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 10
) -> AnalysisListResponse:
    """Lists analyses filtered by user ownership, with search and pagination."""
    query = (
        db.query(Analysis)
        .join(Article, Analysis.article_id == Article.id)
        .filter(Analysis.user_id == user.id, Analysis.is_archived.is_(False))
    )

    if prediction_filter and prediction_filter.upper() in ("FAKE", "REAL"):
        query = query.filter(Analysis.prediction == prediction_filter.upper())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (Article.title.ilike(term)) | (Article.domain.ilike(term))
        )

    total = query.count()
    offset = (max(page, 1) - 1) * limit
    analyses = query.order_by(Analysis.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for a in analyses:
        items.append(
            AnalysisListItem(
                id=a.id,
                title=a.article.title if a.article else "Untitled",
                url=a.article.url if a.article else None,
                prediction=a.prediction,
                label=a.label,
                confidence=a.confidence,
                model_name=a.model_name,
                created_at=a.created_at
            )
        )

    return AnalysisListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )


def get_analysis_by_id(db: Session, analysis_id: int, user: User) -> AnalysisResponse:
    """Retrieves single analysis with authorization check."""
    analysis = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.is_archived.is_(False))
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    if analysis.user_id != user.id and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to access this analysis.")

    explanation = {}
    if analysis.explanation_json:
        try:
            explanation = json.loads(analysis.explanation_json)
        except Exception:
            explanation = {}

    return AnalysisResponse(
        id=analysis.id,
        prediction=analysis.prediction,
        label=analysis.label,
        confidence=analysis.confidence,
        probabilities={
            "fake": analysis.prob_fake,
            "real": analysis.prob_real
        },
        model_name=analysis.model_name,
        model_version=analysis.model_version,
        processing_time_ms=analysis.processing_time_ms,
        explanation=explanation,
        disclaimer="Machine Learning predictions represent statistical text pattern correlation, not definitive factual proof.",
        article=analysis.article,
        created_at=analysis.created_at
    )


def delete_analysis_by_id(db: Session, analysis_id: int, user: User) -> bool:
    """Soft deletes or removes analysis record with authorization check."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    if analysis.user_id != user.id and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete this analysis.")

    db.delete(analysis)
    db.commit()
    return True


def get_user_dashboard_stats(db: Session, user: User) -> DashboardStats:
    """Calculates live analytics from actual database records for user."""
    base_query = db.query(Analysis).filter(Analysis.user_id == user.id, Analysis.is_archived.is_(False))
    total_analyses = base_query.count()

    fake_count = base_query.filter(Analysis.prediction == "FAKE").count()
    authentic_count = base_query.filter(Analysis.prediction == "REAL").count()

    fake_pct = round((fake_count / total_analyses * 100), 1) if total_analyses > 0 else 0.0
    auth_pct = round((authentic_count / total_analyses * 100), 1) if total_analyses > 0 else 0.0

    avg_conf = db.query(func.avg(Analysis.confidence)).filter(
        Analysis.user_id == user.id, Analysis.is_archived.is_(False)
    ).scalar() or 0.0

    # Recent 5 items
    recent_records = (
        base_query.order_by(Analysis.created_at.desc()).limit(5).all()
    )
    recent_items = [
        AnalysisListItem(
            id=a.id,
            title=a.article.title if a.article else "Untitled",
            url=a.article.url if a.article else None,
            prediction=a.prediction,
            label=a.label,
            confidence=a.confidence,
            model_name=a.model_name,
            created_at=a.created_at
        )
        for a in recent_records
    ]

    # Daily trend (last 7 days)
    now = datetime.now(timezone.utc)
    daily_trend = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_fake = (
            base_query.filter(
                Analysis.prediction == "FAKE",
                Analysis.created_at >= day_start,
                Analysis.created_at < day_end
            ).count()
        )
        day_real = (
            base_query.filter(
                Analysis.prediction == "REAL",
                Analysis.created_at >= day_start,
                Analysis.created_at < day_end
            ).count()
        )
        daily_trend.append(
            DayDistribution(
                date=day_start.strftime("%b %d"),
                fake_count=day_fake,
                authentic_count=day_real,
                total=day_fake + day_real
            )
        )

    return DashboardStats(
        total_analyses=total_analyses,
        fake_count=fake_count,
        authentic_count=authentic_count,
        fake_percentage=fake_pct,
        authentic_percentage=auth_pct,
        average_confidence=round(float(avg_conf), 3),
        recent_analyses=recent_items,
        daily_trend=daily_trend
    )

