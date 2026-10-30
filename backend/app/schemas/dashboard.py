from typing import Any, Dict, List
from pydantic import BaseModel
from app.schemas.analysis import AnalysisListItem


class DayDistribution(BaseModel):
    date: str
    fake_count: int
    authentic_count: int
    total: int


class DashboardStats(BaseModel):
    total_analyses: int
    fake_count: int
    authentic_count: int
    fake_percentage: float
    authentic_percentage: float
    average_confidence: float
    recent_analyses: List[AnalysisListItem]
    daily_trend: List[DayDistribution]

