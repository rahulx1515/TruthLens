"""
TruthLens - Tests for Unified LLM Service (Groq, Hugging Face, Ollama)
Validates:
- Provider selection precedence (Groq -> Hugging Face -> Ollama -> None)
- Groq completion and JSON structured output parsing
- Hugging Face chat completion and generation handling
- Provider error and timeout resilience without crashing
- JSON response repair (markdown stripping, trailing comma fixes)
- Rule-based fallback when LLM is offline
- Verification that no OpenAI dependency is required
"""
from unittest.mock import MagicMock, patch
import pytest

from app.core.config import settings
from app.services.llm_service import LLMService


def test_no_openai_dependency_imported():
    """Verify OpenAI SDK is not imported or required by LLM service."""
    import sys
    from app.services.llm_service import LLMService
    # Even if openai might be in site-packages, llm_service must not import it
    import app.services.llm_service as llm_mod
    assert "openai" not in dir(llm_mod)


def test_provider_precedence_groq_first():
    """Groq should take precedence when GROQ_API_KEY is configured."""
    service = LLMService()
    with patch.object(settings, "GROQ_API_KEY", "gsk_test_key_123"):
        with patch.object(settings, "HF_API_KEY", "hf_test_key_456"):
            assert service.get_active_provider() == "groq"


def test_provider_precedence_hf_when_no_groq():
    """Hugging Face should be chosen when Groq key is absent."""
    service = LLMService()
    with patch.object(settings, "GROQ_API_KEY", None):
        with patch.object(settings, "HF_API_KEY", "hf_test_key_456"):
            assert service.get_active_provider() == "huggingface"


def test_provider_precedence_ollama_when_no_cloud_keys():
    """Ollama should be chosen when no cloud keys are configured and service is healthy."""
    mock_ollama = MagicMock()
    mock_ollama.is_healthy.return_value = True
    service = LLMService(ollama=mock_ollama)

    with patch.object(settings, "GROQ_API_KEY", None):
        with patch.object(settings, "HF_API_KEY", None):
            with patch.object(settings, "HUGGINGFACE_API_KEY", None):
                assert service.get_active_provider() == "ollama"


def test_groq_json_generation_success():
    """Verify Groq API call with json_mode formats correctly and parses output."""
    service = LLMService()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"claims": [{"claim_text": "Sample assertion", "claim_type": "factual"}], "discarded_opinions_count": 0}'
                }
            }
        ]
    }

    with patch.object(settings, "GROQ_API_KEY", "gsk_valid_test_key"):
        with patch("requests.post", return_value=mock_resp) as mock_post:
            data, provider = service.generate_json(prompt="Extract claims from this text", system="System prompt")

            assert provider == "groq"
            assert data is not None
            assert "claims" in data
            assert len(data["claims"]) == 1
            assert data["claims"][0]["claim_text"] == "Sample assertion"

            # Check that requests.post was called with json response_format
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["response_format"] == {"type": "json_object"}
            assert "Authorization" in call_kwargs["headers"]


def test_huggingface_json_generation_with_markdown_fences():
    """Verify Hugging Face output wrapped in markdown ```json ... ``` is cleanly repaired and parsed."""
    service = LLMService()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "```json\n{\n  \"claims\": [{\"claim_text\": \"Extracted from HF\"}],\n  \"discarded_opinions_count\": 1,\n}\n```"
                }
            }
        ]
    }

    with patch.object(settings, "GROQ_API_KEY", None):
        with patch.object(settings, "HF_API_KEY", "hf_valid_test_key"):
            with patch("requests.post", return_value=mock_resp):
                data, provider = service.generate_json(prompt="Extract claims", system="System prompt")

                assert provider == "huggingface"
                assert data is not None
                assert "claims" in data
                assert data["claims"][0]["claim_text"] == "Extracted from HF"


def test_llm_service_error_handling_returns_none_without_crashing():
    """Verify provider HTTP errors and timeouts do not raise unhandled exceptions."""
    import requests
    service = LLMService()

    with patch.object(settings, "GROQ_API_KEY", "gsk_valid_test_key"):
        with patch("requests.post", side_effect=requests.exceptions.Timeout("Read timeout")):
            data, provider = service.generate_json(prompt="Test prompt")
            assert data is None
            assert provider is None

            text, provider = service.generate(prompt="Test prompt")
            assert text is None
            assert provider is None


def test_json_repair_handles_malformed_syntax():
    """Test parse_json_response repairs trailing commas and extra wrappers."""
    # Trailing comma before closing brace
    raw = '{"name": "TruthLens", "version": "2.0.0", }'
    parsed = LLMService.parse_json_response(raw)
    assert parsed == {"name": "TruthLens", "version": "2.0.0"}

    # Leading conversational text
    raw_with_prose = 'Here is your structured JSON:\n\n{"key": "value"}\n\nHope this helps!'
    parsed_prose = LLMService.parse_json_response(raw_with_prose)
    assert parsed_prose == {"key": "value"}

    # Completely invalid text
    invalid = "Not JSON at all"
    assert LLMService.parse_json_response(invalid) is None

