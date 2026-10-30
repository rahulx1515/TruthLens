from fastapi import APIRouter
from app.api.v1.endpoints import analyses, analyze, auth, dashboard, models, verify

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["News Prediction"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["Analysis History"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard Analytics"])
api_router.include_router(models.router, prefix="/models", tags=["Model Insights"])
api_router.include_router(verify.router, prefix="/verify", tags=["Evidence-Based Verification"])

