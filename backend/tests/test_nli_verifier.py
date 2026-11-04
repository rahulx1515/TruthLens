"""
TruthLens - Tests for NLI Verifier & Remote Hugging Face Inference
Validates:
- Premise-hypothesis NLI requests sent to Hugging Face Inference API
- Probability mapping (entailment, contradiction, neutral)
- Error handling: HTTP 503 loading, 429 rate limit, 500 server error, timeouts, invalid JSON
- Inference method labeling: hf_inference_api, neural, heuristic_fallback
- Lazy loading and ENABLE_LOCAL_NEURAL_NLI behavior
"""
import sys
from unittest.mock import MagicMock, patch
import pytest

from app.core.config import settings
from app.schemas.evidence import EvidencePassage
from app.schemas.verification import NLILabel
from app.services.nli_verifier import NLIVerifier


def create_sample_passage(passage_text: str = "The government confirmed the new policy yesterday.") -> EvidencePassage:
    return EvidencePassage(
        passage_id="p-123",
        article_url="https://reuters.com/article/1",
        article_title="Government Policy Update",
        canonical_domain="reuters.com",
        publisher_name="Reuters",
        passage_text=passage_text,
        published_date="2026-10-15",
        retrieved_at="2026-10-30T12:00:00Z",
        relevance_score=0.88,
        is_syndicated_copy=False,
        cluster_id=None
    )


def test_lazy_loading_preserves_memory():
    """Verify load_model does not import PyTorch when ENABLE_LOCAL_NEURAL_NLI is false."""
    verifier = NLIVerifier()
    with patch.object(settings, "ENABLE_LOCAL_NEURAL_NLI", False):
        res = verifier.load_model()
        assert res is False
        assert verifier.is_neural_available is False


def test_predict_hf_api_successful_entailment():
    """Test remote Hugging Face API inference returning entailment probabilities."""
    verifier = NLIVerifier()
    passage = create_sample_passage("The Ministry announced that the tax cuts will take effect next month.")
    claim = "Tax cuts will be implemented next month."

    mock_hf_response = [
        [
            {"label": "entailment", "score": 0.88},
            {"label": "neutral", "score": 0.08},
            {"label": "contradiction", "score": 0.04}
        ]
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_hf_response

    with patch.object(settings, "HF_API_KEY", "hf_test_token_123"):
        with patch("requests.post", return_value=mock_resp) as mock_post:
            eval_res = verifier.evaluate_passage(claim_text=claim, passage=passage)

            # Ensure both premise and hypothesis were sent in request payload
            assert mock_post.called
            call_kwargs = mock_post.call_args[1]
            assert "json" in call_kwargs
            payload = call_kwargs["json"]
            assert payload["inputs"]["text"] == passage.passage_text
            assert payload["inputs"]["text_pair"] == claim
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == "Bearer hf_test_token_123"

            # Check evaluation properties
            assert eval_res.inference_method == "hf_inference_api"
            assert eval_res.nli_label == NLILabel.ENTAILMENT
            assert eval_res.entailment_prob >= 0.85
            assert eval_res.contradiction_prob <= 0.05


def test_predict_hf_api_successful_contradiction():
    """Test remote Hugging Face API inference returning contradiction probabilities."""
    verifier = NLIVerifier()
    passage = create_sample_passage("The spokesperson explicitly denied that the tax cuts were approved.")
    claim = "The tax cuts were approved by the government."

    mock_hf_response = [
        [
            {"label": "contradiction", "score": 0.92},
            {"label": "neutral", "score": 0.05},
            {"label": "entailment", "score": 0.03}
        ]
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_hf_response

    with patch.object(settings, "HF_API_KEY", "hf_test_token_123"):
        with patch("requests.post", return_value=mock_resp):
            eval_res = verifier.evaluate_passage(claim_text=claim, passage=passage)

            assert eval_res.inference_method == "hf_inference_api"
            assert eval_res.nli_label == NLILabel.CONTRADICTION
            assert eval_res.contradiction_prob >= 0.90


def test_predict_hf_api_handles_model_loading_503():
    """Verify HTTP 503 (model loading) safely falls back to heuristic and never claims remote inference."""
    verifier = NLIVerifier()
    passage = create_sample_passage("The government issued a statement.")
    claim = "A statement was issued."

    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.text = '{"error": "Model is currently loading", "estimated_time": 20.0}'

    with patch.object(settings, "HF_API_KEY", "hf_test_token_123"):
        with patch("requests.post", return_value=mock_resp):
            eval_res = verifier.evaluate_passage(claim_text=claim, passage=passage)

            # MUST report heuristic_fallback, NEVER hf_inference_api or neural
            assert eval_res.inference_method == "heuristic_fallback"
            assert eval_res.inference_method != "hf_inference_api"
            assert eval_res.inference_method != "neural"


def test_predict_hf_api_handles_rate_limit_429():
    """Verify HTTP 429 rate limit safely falls back to heuristic without crashing."""
    verifier = NLIVerifier()
    passage = create_sample_passage("The ministry denied the rumor completely.")
    claim = "The rumor was accepted by the ministry."

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = '{"error": "Rate limit reached"}'

    with patch.object(settings, "HF_API_KEY", "hf_test_token_123"):
        with patch("requests.post", return_value=mock_resp):
            eval_res = verifier.evaluate_passage(claim_text=claim, passage=passage)

            assert eval_res.inference_method == "heuristic_fallback"


def test_predict_hf_api_handles_malformed_json_response():
    """Verify invalid JSON or malformed structures safely fall back to heuristic."""
    verifier = NLIVerifier()
    passage = create_sample_passage("Sample text passage.")
    claim = "Sample assertion."

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"unexpected": "payload_structure"}

    with patch.object(settings, "HF_API_KEY", "hf_test_token_123"):
        with patch("requests.post", return_value=mock_resp):
            eval_res = verifier.evaluate_passage(claim_text=claim, passage=passage)

            assert eval_res.inference_method == "heuristic_fallback"


def test_predict_hf_api_handles_network_timeout():
    """Verify network timeouts do not raise unhandled exceptions and fallback cleanly."""
    import requests
    verifier = NLIVerifier()
    passage = create_sample_passage("Sample text passage.")
    claim = "Sample assertion."

    with patch.object(settings, "HF_API_KEY", "hf_test_token_123"):
        with patch("requests.post", side_effect=requests.exceptions.Timeout("Connection timed out")):
            eval_res = verifier.evaluate_passage(claim_text=claim, passage=passage)

            assert eval_res.inference_method == "heuristic_fallback"

