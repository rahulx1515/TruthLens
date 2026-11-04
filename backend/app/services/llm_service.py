"""
TruthLens - Unified Cloud & Local LLM Service
Provides resilient LLM inference for claim extraction and report synthesis.
Supports:
1. Groq Cloud (high-speed Llama models via Groq API)
2. Hugging Face Inference API (serverless instruct models)
3. Local Ollama (local llama3.2 on CPU)
4. Safe fallback to deterministic rules when LLM is unavailable

Ensures provider errors and timeouts do not crash the verification workflow.
Zero OpenAI API dependencies (uses standard requests/httpx).
"""
import json
import logging
import re
import time
from typing import Any, Dict, Optional, Tuple

import requests

from app.core.config import settings
from app.ml.ollama_client import OllamaClient, ollama_client

logger = logging.getLogger("truthlens.llm")


class LLMService:
    """
    Unified LLM router for cloud and local inference.
    Prioritizes configured cloud providers (Groq, Hugging Face) for production
    and local Ollama for development.
    """

    def __init__(self, ollama: Optional[OllamaClient] = None):
        self.ollama = ollama or ollama_client
        self.timeout = min(getattr(settings, "LLM_TIMEOUT_SECONDS", 30), 45)
        self._last_ollama_check: float = 0.0
        self._last_ollama_status: bool = False

    def _is_ollama_healthy(self) -> bool:
        """Caches Ollama health checks for 5 seconds to prevent repeated connection latency."""
        now = time.time()
        if now - self._last_ollama_check < 5.0:
            return self._last_ollama_status
        self._last_ollama_check = now
        try:
            self._last_ollama_status = bool(self.ollama.is_healthy())
        except Exception:
            self._last_ollama_status = False
        return self._last_ollama_status

    @property
    def groq_api_key(self) -> Optional[str]:
        return getattr(settings, "GROQ_API_KEY", None)

    @property
    def groq_model(self) -> str:
        return getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")

    @property
    def hf_api_key(self) -> Optional[str]:
        return getattr(settings, "HF_API_KEY", None) or getattr(settings, "HUGGINGFACE_API_KEY", None)

    @property
    def hf_model(self) -> str:
        return getattr(settings, "HUGGINGFACE_MODEL", "meta-llama/Llama-3.2-3B-Instruct")

    def get_active_provider(self) -> Optional[str]:
        """
        Determines the highest priority available LLM provider.
        Precedence:
        1. Explicit LLM_PROVIDER if set ('groq', 'huggingface', 'ollama')
        2. Groq (if GROQ_API_KEY is configured)
        3. Hugging Face (if HF_API_KEY/HUGGINGFACE_API_KEY is configured)
        4. Local Ollama (if service is healthy and reachable)
        5. None (trigger deterministic rule-based fallback)
        """
        forced = getattr(settings, "LLM_PROVIDER", "auto")
        if forced == "none":
            return None

        if forced == "groq" and self.groq_api_key:
            return "groq"
        if forced in ("huggingface", "hf") and self.hf_api_key:
            return "huggingface"
        if forced == "ollama" and self._is_ollama_healthy():
            return "ollama"

        # Auto-selection
        if self.groq_api_key:
            return "groq"
        if self.hf_api_key:
            return "huggingface"
        if self._is_ollama_healthy():
            return "ollama"

        return None

    def is_available(self) -> bool:
        """Returns True if any valid LLM provider is available."""
        return self.get_active_provider() is not None

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.1
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generates free-form text using the active LLM provider.
        Returns (generated_text, provider_name) or (None, None) on failure.
        Never raises exceptions to caller.
        """
        provider = self.get_active_provider()
        if not provider:
            return None, None

        try:
            if provider == "groq":
                text = self._call_groq(prompt, system=system, max_tokens=max_tokens, temperature=temperature, json_mode=False)
                return text, "groq"
            elif provider == "huggingface":
                text = self._call_huggingface(prompt, system=system, max_tokens=max_tokens, temperature=temperature, json_mode=False)
                return text, "huggingface"
            elif provider == "ollama":
                res = self.ollama.generate(
                    prompt=prompt,
                    system=system,
                    options={"num_predict": max_tokens, "temperature": temperature}
                )
                return res.get("response", "").strip(), "ollama"
        except Exception as e:
            logger.warning(f"LLM generation failed via provider '{provider}': {e}")
            return None, None

        return None, None

    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Generates structured JSON using the active LLM provider with robust JSON repair.
        Returns (parsed_json_dict, provider_name) or (None, None) on failure.
        Never raises exceptions to caller.
        """
        provider = self.get_active_provider()
        if not provider:
            return None, None

        try:
            raw_text = None
            if provider == "groq":
                raw_text = self._call_groq(prompt, system=system, max_tokens=max_tokens, temperature=0.1, json_mode=True)
            elif provider == "huggingface":
                raw_text = self._call_huggingface(prompt, system=system, max_tokens=max_tokens, temperature=0.1, json_mode=True)
            elif provider == "ollama":
                # Ollama client has native JSON parsing
                try:
                    data = self.ollama.generate_json(prompt=prompt, system=system)
                    if isinstance(data, dict):
                        return data, "ollama"
                except Exception as e:
                    logger.warning(f"Ollama JSON generation failed: {e}")
                    return None, None

            if raw_text:
                parsed = self.parse_json_response(raw_text)
                if parsed:
                    return parsed, provider

        except Exception as e:
            logger.warning(f"LLM JSON generation failed via provider '{provider}': {e}")
            return None, None

        return None, None

    def _call_groq(
        self,
        prompt: str,
        system: Optional[str],
        max_tokens: int,
        temperature: float,
        json_mode: bool
    ) -> Optional[str]:
        """Calls Groq Cloud OpenAI-compatible completion API using requests (no OpenAI SDK)."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.groq_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        if resp.status_code != 200:
            logger.warning(f"Groq API returned HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        data = resp.json()
        choices = data.get("choices", [])
        if choices and "message" in choices[0]:
            return choices[0]["message"].get("content", "").strip()
        return None

    def _call_huggingface(
        self,
        prompt: str,
        system: Optional[str],
        max_tokens: int,
        temperature: float,
        json_mode: bool
    ) -> Optional[str]:
        """Calls Hugging Face Inference API for text generation."""
        headers = {
            "Authorization": f"Bearer {self.hf_api_key}",
            "Content-Type": "application/json"
        }

        # Try Hugging Face Chat Completions endpoint first
        chat_url = f"https://api-inference.huggingface.co/models/{self.hf_model}/v1/chat/completions"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if json_mode and not system:
            messages.append({"role": "system", "content": "You must output valid JSON only."})
        messages.append({"role": "user", "content": prompt})

        chat_payload = {
            "model": self.hf_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            resp = requests.post(chat_url, json=chat_payload, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "").strip()
        except Exception:
            pass

        # Fallback to standard HF model endpoint
        standard_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
        combined_prompt = f"{system}\n\n{prompt}" if system else prompt
        if json_mode:
            combined_prompt += "\nOutput valid JSON only:"

        gen_payload = {
            "inputs": combined_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "return_full_text": False
            }
        }

        resp = requests.post(standard_url, json=gen_payload, headers=headers, timeout=self.timeout)
        if resp.status_code != 200:
            logger.warning(f"HF Generation API returned HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        data = resp.json()
        if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()
        elif isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()

        return None

    @staticmethod
    def parse_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Cleans markdown wrappers, isolates JSON blocks, and fixes common syntax issues.
        Never raises exceptions on malformed input.
        """
        if not raw_text or not raw_text.strip():
            return None

        text = raw_text.strip()

        # Remove markdown code block markers
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        # Direct parse attempt
        try:
            res = json.loads(text)
            if isinstance(res, dict):
                return res
        except Exception:
            pass

        # Extract innermost or outermost JSON object {...}
        match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if match:
            candidate = match.group(1).strip()
            # Clean trailing commas: ,} -> } and ,] -> ]
            candidate = re.sub(r",\s*\}", "}", candidate)
            candidate = re.sub(r",\s*\]", "]", candidate)
            try:
                res = json.loads(candidate)
                if isinstance(res, dict):
                    return res
            except Exception:
                pass

        logger.warning(f"Unable to parse LLM response into JSON: {raw_text[:150]}...")
        return None


# Global singleton
llm_service = LLMService()
