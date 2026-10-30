"""
Tests for TruthLens ML Predictor and Explainable AI Attributions
"""
import pytest
from app.ml.predictor import NewsPredictor, get_predictor


@pytest.fixture(scope="module")
def predictor():
    return get_predictor()


def test_predictor_initialization(predictor):
    assert predictor.vectorizer is not None
    assert predictor.primary_model is not None
    assert len(predictor.feature_names) == 10000
    assert "logistic_regression" in predictor.get_supported_models()


def test_predict_authentic_news(predictor):
    title = "WASHINGTON (Reuters) - Federal Reserve leaves interest rates unchanged"
    text = "WASHINGTON (Reuters) - The U.S. Federal Reserve held benchmark interest rates steady on Wednesday as economic indicators showed steady job growth."
    
    result = predictor.predict(title=title, text=text, model_name="logistic_regression")
    
    assert result["prediction"] == "REAL"
    assert result["label"] == "Likely Authentic"
    assert result["confidence"] > 0.85
    assert result["probabilities"]["real"] > 0.50
    assert result["processing_time_ms"] > 0
    assert "explanation" in result
    assert len(result["explanation"]["top_real_indicators"]) > 0


def test_predict_fake_news(predictor):
    title = "OMG! Secret Alien Base Discovered Under the White House!"
    text = "Shocking leaked government memo proves extraterrestrial beings are running the government in complete secrecy and brainwashing citizens."
    
    result = predictor.predict(title=title, text=text, model_name="logistic_regression")
    
    assert result["prediction"] == "FAKE"
    assert result["label"] == "Likely Fake"
    assert result["confidence"] > 0.70
    assert result["probabilities"]["fake"] > 0.50
    assert len(result["explanation"]["top_fake_indicators"]) > 0


def test_predict_with_random_forest(predictor):
    if "random_forest" in predictor.get_supported_models():
        title = "LONDON (Reuters) - Prime Minister announces new climate investment"
        text = "LONDON (Reuters) - Britain unveiled a multi-billion dollar clean energy plan on Thursday aimed at cutting emissions."
        
        result = predictor.predict(title=title, text=text, model_name="random_forest")
        assert result["model_name"] == "Random Forest"
        assert result["prediction"] in ("REAL", "FAKE")


def test_predict_empty_content_graceful_handling(predictor):
    result = predictor.predict(title="", text="")
    assert result["prediction"] == "UNKNOWN"
    assert result["label"] == "Inconclusive"
    assert result["confidence"] == 0.50

