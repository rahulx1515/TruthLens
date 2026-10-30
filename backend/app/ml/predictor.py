"""
TruthLens - Machine Learning Predictor Service
Loads trained model artifacts, performs inference with unified preprocessing,
and computes feature attributions for Explainable AI (XAI).
"""
import json
import os
import time
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
from app.ml.preprocessing import preprocess_news


class NewsPredictor:
    """
    Production predictor for Fake News classification with Explainable AI attribution.
    """

    def __init__(self, artifacts_dir: Optional[str] = None):
        if artifacts_dir is None:
            # Default to relative path from this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            artifacts_dir = os.path.join(current_dir, "artifacts")
        
        self.artifacts_dir = artifacts_dir
        self.primary_model_path = os.path.join(artifacts_dir, "fake_news_model.joblib")
        self.rf_model_path = os.path.join(artifacts_dir, "rf_model.joblib")
        self.vectorizer_path = os.path.join(artifacts_dir, "tfidf_vectorizer.joblib")
        self.metadata_path = os.path.join(artifacts_dir, "model_metadata.json")

        self.vectorizer = None
        self.primary_model = None
        self.rf_model = None
        self.metadata = {}
        self.feature_names = None

        self._load_artifacts()

    def _load_artifacts(self):
        """Loads vectorizer, models, and metadata into memory."""
        if not os.path.exists(self.vectorizer_path):
            raise FileNotFoundError(f"TF-IDF vectorizer artifact missing at {self.vectorizer_path}")
        if not os.path.exists(self.primary_model_path):
            raise FileNotFoundError(f"Primary model artifact missing at {self.primary_model_path}")

        self.vectorizer = joblib.load(self.vectorizer_path)
        self.primary_model = joblib.load(self.primary_model_path)
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())

        if os.path.exists(self.rf_model_path):
            try:
                self.rf_model = joblib.load(self.rf_model_path)
            except Exception as e:
                print(f"Warning: Failed to load RF model: {e}")

        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    def get_supported_models(self) -> List[str]:
        """Returns list of available model identifiers."""
        models = ["logistic_regression"]
        if self.rf_model is not None:
            models.append("random_forest")
        return models

    def predict(
        self,
        title: Optional[str] = "",
        text: Optional[str] = "",
        model_name: Optional[str] = "logistic_regression"
    ) -> Dict[str, Any]:
        """
        Executes prediction pipeline on raw news text:
        1. Preprocess using deterministic pipeline
        2. Vectorize using pre-fitted TF-IDF
        3. Model probability prediction
        4. Feature attribution (Explainable AI)
        5. Calibration and metadata enrichment
        """
        start_time = time.perf_counter()

        # Handle empty text edge case
        cleaned_text = preprocess_news(title, text)
        if not cleaned_text:
            return {
                "prediction": "UNKNOWN",
                "label": "Inconclusive",
                "confidence": 0.50,
                "probabilities": {"fake": 0.50, "real": 0.50},
                "model_name": model_name or "logistic_regression",
                "model_version": self.metadata.get("version", "1.0.0"),
                "processing_time_ms": round((time.perf_counter() - start_time) * 1000, 2),
                "explanation": {
                    "top_fake_indicators": [],
                    "top_real_indicators": [],
                    "summary": "Insufficient textual content to perform analysis. Please provide more detailed news text."
                },
                "disclaimer": "Machine Learning predictions represent statistical text pattern correlation, not definitive factual proof."
            }

        # Select model
        selected_key = (model_name or "logistic_regression").lower().strip()
        if selected_key in ["random_forest", "rf"] and self.rf_model is not None:
            active_model = self.rf_model
            resolved_model_name = "Random Forest"
        else:
            active_model = self.primary_model
            resolved_model_name = "Logistic Regression"

        # Transform using pre-fitted vectorizer (NEVER fit during inference)
        X_vec = self.vectorizer.transform([cleaned_text])

        # Predict probabilities
        # Class 0: Fake, Class 1: Real
        probabilities = active_model.predict_proba(X_vec)[0]
        prob_fake = float(probabilities[0])
        prob_real = float(probabilities[1])

        if prob_fake >= prob_real:
            prediction = "FAKE"
            label = "Likely Fake"
            confidence = prob_fake
        else:
            prediction = "REAL"
            label = "Likely Authentic"
            confidence = prob_real

        # Explainable AI Feature Attribution
        explanation = self._explain_prediction(X_vec, cleaned_text, active_model, resolved_model_name)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return {
            "prediction": prediction,
            "label": label,
            "confidence": round(confidence, 4),
            "probabilities": {
                "fake": round(prob_fake, 4),
                "real": round(prob_real, 4)
            },
            "model_name": resolved_model_name,
            "model_version": self.metadata.get("version", "1.0.0"),
            "processing_time_ms": round(elapsed_ms, 2),
            "explanation": explanation,
            "disclaimer": "Machine Learning predictions represent statistical text pattern correlation, not definitive factual proof."
        }

    def _explain_prediction(
        self,
        X_vec,
        cleaned_text: str,
        model,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Explainable AI: Identifies influential tokens and directional contribution
        towards Fake vs Real prediction using model weights / feature contributions.
        """
        # Find active features in document
        coo = X_vec.tocoo()
        if coo.nnz == 0:
            return {
                "top_fake_indicators": [],
                "top_real_indicators": [],
                "summary": "No registered vocabulary terms were detected in the input."
            }

        feature_indices = coo.col
        tfidf_values = coo.data
        words = self.feature_names[feature_indices]

        if hasattr(model, "coef_"):
            # Linear model (Logistic Regression): contribution = tfidf * weight
            coefficients = model.coef_[0][feature_indices]
            contributions = tfidf_values * coefficients
        elif hasattr(model, "feature_importances_"):
            # Tree model (Random Forest): use feature importances modulated by tfidf
            importances = model.feature_importances_[feature_indices]
            contributions = tfidf_values * importances
        else:
            contributions = tfidf_values

        items = []
        for word, val, contrib in zip(words, tfidf_values, contributions):
            items.append({
                "word": word,
                "importance": round(float(abs(contrib)), 4),
                "contribution": round(float(contrib), 4),
                "direction": "real" if contrib > 0 else "fake"
            })

        # Sort items
        real_indicators = sorted([i for i in items if i["direction"] == "real"], key=lambda x: x["importance"], reverse=True)[:6]
        fake_indicators = sorted([i for i in items if i["direction"] == "fake"], key=lambda x: x["importance"], reverse=True)[:6]

        # Natural language summary
        if len(fake_indicators) > len(real_indicators):
            summary = (
                f"The text exhibits stylistic markers and keyword clusters frequently observed in fabricated news, "
                f"most notably: '{', '.join(k['word'] for k in fake_indicators[:3])}'."
            )
        else:
            summary = (
                f"The text exhibits formal journalistic phrasing and attribution characteristics typical of verified news reporting, "
                f"such as: '{', '.join(k['word'] for k in real_indicators[:3])}'."
            )

        return {
            "top_fake_indicators": fake_indicators,
            "top_real_indicators": real_indicators,
            "summary": summary
        }


# Global singleton instance
_predictor_instance = None


def get_predictor() -> NewsPredictor:
    """Returns singleton NewsPredictor instance."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = NewsPredictor()
    return _predictor_instance

