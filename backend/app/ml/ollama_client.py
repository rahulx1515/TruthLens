"""
TruthLens - Local Ollama AI Client
Handles communication with local Ollama service for claim extraction,
search query formulation, and structured report synthesis.
Enforces deterministic parameters, keep_alive model retention, CPU bounds,
and robust JSON schema compliance.
"""
import json
import logging
import re
import time
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
    Optimized for CPU inference on 16GB RAM machines.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL
        # Use calibrated timeout: 30 seconds default to prevent 60s hangs on CPU
        self.timeout = timeout or min(settings.OLLAMA_TIMEOUT_SECONDS, 35)
        self.last_latency_ms: float = 0.0
        self._is_warmed_up: bool = False

    def is_healthy(self) -> bool:
        """Check if local Ollama server is running and responding quickly."""
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def warmup(self) -> bool:
        """
        Preloads model into RAM with keep_alive='30m' so first user request
        does not incur a cold-start model load penalty.
        """
        if self._is_warmed_up or not self.is_healthy():
            return False
        try:
            payload = {
                "model": self.model_name,
                "prompt": "ping",
                "keep_alive": "30m",
                "stream": False,
                "options": {
                    "num_predict": 1,
                    "num_thread": settings.OLLAMA_NUM_THREADS
                }
            }
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    self._is_warmed_up = True
                    logger.info(f"Ollama model {self.model_name} warmed up and kept resident in memory.")
                    return True
        except Exception as e:
            logger.debug(f"Ollama warmup skipped: {e}")
        return False

    def list_models(self) -> List[str]:
        """List all available models loaded in local Ollama."""
        try:
            with httpx.Client(timeout=3.0) as client:
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
        Send a completion generation request to Ollama with CPU bounds and keep_alive.
        """
        start_t = time.time()
        opts = {
            "temperature": temperature,
            "top_p": 0.9,
            "num_thread": settings.OLLAMA_NUM_THREADS,
            "num_predict": 512,  # Bounded generation prevents runaway tokens
            "num_ctx": 2048,     # Bounded context fits CPU inference
        }
        if options:
            opts.update(options)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "keep_alive": "30m",  # Keep model in RAM to eliminate cold-start reloads
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
                self.last_latency_ms = round((time.time() - start_t) * 1000, 2)
                if resp.status_code != 200:
                    raise OllamaGenerationError(
                        f"Ollama returned HTTP {resp.status_code}: {resp.text}"
                    )
                return resp.json()
        except httpx.ConnectError as e:
            self.last_latency_ms = round((time.time() - start_t) * 1000, 2)
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            self.last_latency_ms = round((time.time() - start_t) * 1000, 2)
            raise OllamaTimeoutError(f"Ollama generation timed out after {self.timeout}s: {e}")
        except Exception as e:
            self.last_latency_ms = round((time.time() - start_t) * 1000, 2)
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

        # Extract embedded JSON if model output conversational preamble
        json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
        if json_match:
            cleaned = json_match.group(1)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            logger.error(f"Failed to decode Ollama JSON output: {raw_text[:200]}")
            raise OllamaGenerationError(f"Invalid JSON returned by Ollama: {err}")

    def get_embedding(
        self,
        text: str,
        embedding_model: str = "nomic-embed-text:latest"
    ) -> List[float]:
        """Retrieve dense vector embedding for text using Ollama."""
        payload = {
            "model": embedding_model,
            "prompt": text,
            "keep_alive": "30m"
        }
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(f"{self.base_url}/api/embeddings", json=payload)
                if resp.status_code == 200:
                    return resp.json().get("embedding", [])
                raise OllamaGenerationError(f"Embeddings API error {resp.status_code}: {resp.text}")
        except Exception as e:
            raise OllamaGenerationError(f"Embedding generation failed: {e}")


# Singleton client
ollama_client = OllamaClient()
