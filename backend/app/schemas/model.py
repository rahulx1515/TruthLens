from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ConfusionMatrixDetails(BaseModel):
    true_negative: int
    false_positive: int
    false_negative: int
    true_positive: int
    positive_label: str = "Real"
    negative_label: str = "Fake"
    matrix: List[List[int]]


class ModelBenchmarkItem(BaseModel):
    key: str
    name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    latency_ms: float
    confusion_matrix: Optional[ConfusionMatrixDetails] = None


class ModelsOverviewResponse(BaseModel):
    selected_production_model: str
    supported_models: List[str]
    selection_rationale: str
    dataset: str
    vocabulary_size: int
    models: List[ModelBenchmarkItem]

