from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.article import ArticleOut


class AnalysisRequest(BaseModel):
    title: Optional[str] = Field(default="", description="News article headline")
    text: Optional[str] = Field(default="", description="News article full text body")
    url: Optional[str] = Field(default=None, description="Optional news article URL to scrape and analyze")
    model_name: Optional[str] = Field(default="logistic_regression", description="Selected ML model engine")


class IndicatorWord(BaseModel):
    word: str
    importance: float
    contribution: float
    direction: str  # "fake" or "real"


class ExplanationDetail(BaseModel):
    top_fake_indicators: List[IndicatorWord] = []
    top_real_indicators: List[IndicatorWord] = []
    summary: str


class Probabilities(BaseModel):
    fake: float
    real: float


class AnalysisResponse(BaseModel):
    id: Optional[int] = None
    prediction: str  # "FAKE" or "REAL"
    label: str       # "Likely Fake" or "Likely Authentic"
    confidence: float
    probabilities: Probabilities
    model_name: str
    model_version: str
    processing_time_ms: float
    explanation: ExplanationDetail
    disclaimer: str
    article: Optional[ArticleOut] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisListItem(BaseModel):
    id: int
    title: Optional[str]
    url: Optional[str]
    prediction: str
    label: str
    confidence: float
    model_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisListResponse(BaseModel):
    items: List[AnalysisListItem]
    total: int
    page: int
    limit: int

