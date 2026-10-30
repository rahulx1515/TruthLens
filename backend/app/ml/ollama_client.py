"""
TruthLens 2.0 - Local Ollama AI Client
Handles communication with local Ollama service for claim extraction,
search query formulation, and structured report synthesis.
Enforces deterministic parameters and JSON schema compliance.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("truthlens.ollama")


class OllamaError(Exception):
    """Base exception for Ollama client errors."""
    pass


class OllamaConnectionError(OllamaError):
    """Raised when Ollama server is unreachable."""
    pass


class OllamaTimeoutError(OllamaError):
    """Raised when Ollama inference times out."""
    pass


class OllamaGenerationError(OllamaError):
    """Raised when generation fails or JSON output cannot be parsed."""
    pass


class OllamaClient:
    """
    Client for interacting with local Ollama instance (default: http://127.0.0.1:11434).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    def is_healthy(self) -> bool:
        """Check if local Ollama server is running and responding."""
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """List all available models loaded in local Ollama."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("name", "") for m in data.get("models", [])]
                return []
        except Exception as e:
            logger.warning(f"Failed to query Ollama models: {e}")
            return []

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format_type: Optional[str] = None,
        temperature: float = 0.1,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a completion generation request to Ollama.
        """
        opts = {
            "temperature": temperature,
            "top_p": 0.9,
            "num_thread": settings.OLLAMA_NUM_THREADS,
        }
        if options:
            opts.update(options)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": opts,
        }
        if system:
            payload["system"] = system
        if format_type:
            payload["format"] = format_type

        try:
            with httpx.Client(timeout=float(self.timeout)) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code != 200:
                    raise OllamaGenerationError(
                        f"Ollama returned HTTP {resp.status_code}: {resp.text}"
                    )
                return resp.json()
        except httpx.ConnectError as e:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(f"Ollama generation timed out after {self.timeout}s: {e}")
        except Exception as e:
            raise OllamaGenerationError(f"Error during Ollama generation: {e}")

    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Generates structured JSON from Ollama with markdown stripping and robust repair.
        """
        resp = self.generate(
            prompt=prompt,
            system=system,
            format_type="json",
            temperature=temperature
        )
        raw_text = resp.get("response", "").strip()
        
        # Clean potential markdown fences (```json ... ```)
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            logger.error(f"Failed to decode Ollama JSON output: {raw_text}")
            raise OllamaGenerationError(f"Invalid JSON returned by Ollama: {err}")

    def get_embedding(
        self,
        text: str,
        embedding_model: str = "nomic-embed-text:latest"
    ) -> List[float]:
        """Retrieve dense vector embedding for text using Ollama."""
        payload = {
            "model": embedding_model,
            "prompt": text
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{self.base_url}/api/embeddings", json=payload)
                if resp.status_code == 200:
                    return resp.json().get("embedding", [])
                raise OllamaGenerationError(f"Embeddings API error {resp.status_code}: {resp.text}")
        except Exception as e:
            raise OllamaGenerationError(f"Embedding generation failed: {e}")


# Singleton client
ollama_client = OllamaClient()

