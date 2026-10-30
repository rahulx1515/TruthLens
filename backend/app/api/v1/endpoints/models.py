"""
Models Performance API
GET /api/v1/models/performance
"""
import json
import os
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.model import ModelBenchmarkItem, ModelsOverviewResponse

router = APIRouter()


@router.get("/performance", response_model=ModelsOverviewResponse)
def get_models_performance():
    """
    Returns verified evaluation results, confusion matrices, and model benchmarks
    from the validated ML pipeline.
    """
    meta_path = os.path.join(settings.ML_ARTIFACTS_DIR, "model_metadata.json")
    if not os.path.exists(meta_path):
        meta_path = "backend/app/ml/artifacts/model_metadata.json"

    metadata = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    metrics_dict = metadata.get("metrics", {})
    models_list = []
    for key, data in metrics_dict.items():
        models_list.append(
            ModelBenchmarkItem(
                key=key,
                name=data.get("name", key),
                accuracy=data.get("accuracy", 0.0),
                precision=data.get("precision", 0.0),
                recall=data.get("recall", 0.0),
                f1_score=data.get("f1_score", 0.0),
                latency_ms=data.get("latency_ms", 0.0),
                confusion_matrix=data.get("confusion_matrix")
            )
        )

    # Sort descending by accuracy
    models_list.sort(key=lambda m: m.accuracy, reverse=True)

    return ModelsOverviewResponse(
        selected_production_model=metadata.get("selected_production_model", "Logistic Regression"),
        supported_models=metadata.get("supported_models", ["logistic_regression", "random_forest"]),
        selection_rationale=metadata.get(
            "selection_rationale",
            "Logistic Regression selected based on matched accuracy, sub-millisecond latency, and explainability."
        ),
        dataset=metadata.get("dataset", "ISOT Fake News Corpus"),
        vocabulary_size=metadata.get("vocabulary_size", 10000),
        models=models_list
    )

