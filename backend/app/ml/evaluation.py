"""
TruthLens - Machine Learning Evaluation Module
Calculates performance metrics, confusion matrices, classification reports,
and persists comparative benchmarks.
"""
import json
import os
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


class ModelEvaluator:
    """
    Evaluator for text classification models, calculating standard NLP metrics
    and producing structured performance summaries for API and Dashboard consumption.
    """

    @staticmethod
    def evaluate_predictions(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Calculates accuracy, precision, recall, F1, confusion matrix and detailed report.
        """
        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        
        cm = confusion_matrix(y_true, y_pred)
        # [[TN, FP], [FN, TP]] where 0=Fake, 1=Real
        tn, fp, fn, tp = [int(val) for val in cm.ravel()]
        
        clf_rep = classification_report(
            y_true,
            y_pred,
            target_names=["Fake", "Real"],
            output_dict=True,
            zero_division=0
        )
        
        return {
            "model_name": model_name,
            "accuracy": round(acc * 100, 2),
            "precision": round(prec * 100, 2),
            "recall": round(rec * 100, 2),
            "f1_score": round(f1 * 100, 2),
            "confusion_matrix": {
                "true_negative": tn,  # Predicted Fake, Actually Fake
                "false_positive": fp, # Predicted Real, Actually Fake
                "false_negative": fn, # Predicted Fake, Actually Real
                "true_positive": tp,  # Predicted Real, Actually Real
                "matrix": cm.tolist()
            },
            "classification_report": clf_rep,
            "sample_count": len(y_true)
        }

    @staticmethod
    def load_benchmark_results(results_csv_path: str) -> List[Dict[str, Any]]:
        """
        Loads CSV comparison results and parses them into a list of model records.
        """
        if not os.path.exists(results_csv_path):
            return []
        
        df = pd.read_csv(results_csv_path)
        records = []
        for _, row in df.iterrows():
            records.append({
                "model_name": str(row.get("Model", "")),
                "accuracy": float(row.get("Accuracy", 0.0)),
                "precision": float(row.get("Precision", 0.0)),
                "recall": float(row.get("Recall", 0.0)),
                "f1_score": float(row.get("F1-Score", 0.0))
            })
        return records

