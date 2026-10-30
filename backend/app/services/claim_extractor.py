"""
TruthLens 2.0 - Claim Extraction Engine
Decomposes submitted articles, headlines, or claims into atomic verifiable assertions.
Extracts entities, metrics, and formulates dual search queries (neutral & counter-hypothesis).
Supports English and Hindi natively with an Ollama LLM pipeline and rule-based fallback.
"""
import hashlib
import logging
import re
import time
from typing import List, Optional, Tuple
import uuid

from app.core.config import settings
from app.ml.ollama_client import OllamaClient, ollama_client
from app.nlp.normalizers import get_normalizer
from app.nlp.registry import language_registry
from app.schemas.claim import ClaimExtractionResponse, ClaimType, ExtractedClaim

logger = logging.getLogger("truthlens.claim_extractor")


class ClaimExtractor:
    """
    Extracts atomic, verifiable claims from multilingual news content.
    """

    def __init__(self, client: Optional[OllamaClient] = None):
        self.ollama = client or ollama_client

    def extract_claims(self, text: str, headline: Optional[str] = None) -> ClaimExtractionResponse:
        """
        Main entry point for claim extraction.
        Combines headline and text, detects language, and extracts atomic claims.
        """
        start_time = time.time()
        combined_text = f"{headline.strip() + '. ' if headline else ''}{text.strip()}".strip()

        if not combined_text:
            return ClaimExtractionResponse(
                language="en",
                is_code_mixed=False,
                original_text="",
                claims=[],
                total_claims=0,
                discarded_opinions_count=0,
                processing_time_ms=0.0
            )

        # Step 1: Language and Script Detection
        lang, confidence, is_code_mixed = language_registry.detect_language(combined_text)
        normalizer = get_normalizer(lang)
        normalized_text = normalizer.normalize(combined_text)

        # Step 2: Extract claims via Ollama (or fallback)
        claims = []
        discarded_opinions = 0

        # Try LLM-based extraction first
        if self.ollama.is_healthy():
            try:
                claims, discarded_opinions = self._extract_with_llm(
                    normalized_text, lang=lang, is_code_mixed=is_code_mixed
                )
            except Exception as e:
                logger.warning(f"Ollama claim extraction failed ({e}), using rule-based fallback")
                claims, discarded_opinions = self._extract_with_rules(normalized_text, lang)
        else:
            claims, discarded_opinions = self._extract_with_rules(normalized_text, lang)

        # If LLM returned empty list on non-empty input, run rule-based fallback
        if not claims and len(normalized_text.split()) >= 3:
            claims, discarded_opinions = self._extract_with_rules(normalized_text, lang)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return ClaimExtractionResponse(
            language=lang,
            is_code_mixed=is_code_mixed,
            original_text=combined_text,
            claims=claims,
            total_claims=len(claims),
            discarded_opinions_count=discarded_opinions,
            processing_time_ms=elapsed_ms
        )

    def _extract_with_llm(
        self, text: str, lang: str, is_code_mixed: bool
    ) -> Tuple[List[ExtractedClaim], int]:
        """Extract claims using local Ollama model with structured JSON enforcement."""
        if lang == "hi":
            system_prompt = (
                "You are an expert multilingual factual news verification engine for TruthLens. "
                "Analyze the Hindi or Hinglish text and extract atomic, checkable factual claims. "
                "Strict requirements:\n"
                "1. Maintain authentic Devanagari Unicode script without transliteration or character loss.\n"
                "2. Separate checkable factual claims from subjective opinions or rhetoric.\n"
                "3. For each claim, formulate a neutral search query and a counter-hypothesis query (including 'तथ्य जांच' or 'फर्जी दावा').\n"
                "4. Output strict JSON only matching the schema."
            )
            prompt = f"""Extract checkable claims from this Hindi news text:
\"\"\"{text}\"\"\"

Output valid JSON matching:
{{
  "claims": [
    {{
      "claim_text": "atomic factual claim in Hindi",
      "claim_type": "factual",
      "entities": ["entity1", "entity2"],
      "dates_or_numbers": ["dates or statistics"],
      "neutral_search_query": "neutral search query",
      "counter_search_query": "counter or fact-check query"
    }}
  ],
  "discarded_opinions_count": 0
}}"""
        else:
            system_prompt = (
                "You are an expert factual news verification engine for TruthLens. "
                "Analyze the English news text and extract atomic, checkable factual claims. "
                "Strict requirements:\n"
                "1. Deconstruct complex paragraphs into individual, falsifiable statements.\n"
                "2. Classify each claim: 'factual', 'numerical', 'quote', 'opinion', or 'prediction'.\n"
                "3. Exclude pure subjective opinions.\n"
                "4. Formulate a neutral search query (to find evidence) and a counter-hypothesis query (to find debunks/fact-checks).\n"
                "5. Output strict JSON only matching the schema."
            )
            prompt = f"""Extract checkable claims from this English news text:
\"\"\"{text}\"\"\"

Output valid JSON matching:
{{
  "claims": [
    {{
      "claim_text": "atomic factual assertion",
      "claim_type": "factual",
      "entities": ["entity1", "entity2"],
      "dates_or_numbers": ["dates or statistics"],
      "neutral_search_query": "neutral search query",
      "counter_search_query": "counter or debunk search query"
    }}
  ],
  "discarded_opinions_count": 0
}}"""

        data = self.ollama.generate_json(prompt=prompt, system=system_prompt)
        raw_claims = data.get("claims", [])
        discarded = int(data.get("discarded_opinions_count", 0))

        valid_claims = []
        for idx, item in enumerate(raw_claims):
            claim_text = item.get("claim_text", "").strip()
            if not claim_text or len(claim_text) < 10:
                continue

            claim_type_str = item.get("claim_type", "factual").lower()
            if claim_type_str == "opinion":
                discarded += 1
                continue

            try:
                ctype = ClaimType(claim_type_str)
            except ValueError:
                ctype = ClaimType.FACTUAL

            claim_id = self._generate_claim_id(claim_text)
            neutral_q = item.get("neutral_search_query", "").strip() or claim_text
            counter_q = item.get("counter_search_query", "").strip()
            if not counter_q:
                counter_q = f"{claim_text} fact check debunk false"

            valid_claims.append(
                ExtractedClaim(
                    id=claim_id,
                    claim_text=claim_text,
                    claim_type=ctype,
                    entities=item.get("entities", []),
                    dates_or_numbers=item.get("dates_or_numbers", []),
                    neutral_search_query=neutral_q,
                    counter_search_query=counter_q,
                    language=lang,
                    is_verifiable=True
                )
            )

        return valid_claims, discarded

    def _extract_with_rules(self, text: str, lang: str) -> Tuple[List[ExtractedClaim], int]:
        """
        Deterministic rule-based claim extraction used as reliable fallback.
        Preserves complete functionality even if local LLM is temporarily unavailable.
        """
        normalizer = get_normalizer(lang)
        sentences = normalizer.split_sentences(text)

        opinion_cues_en = {"i think", "i believe", "in my view", "in my opinion", "personally", "it seems", "probably"}
        opinion_cues_hi = {"मुझे लगता है", "मेरी राय में", "शायद", "हो सकता है"}

        claims = []
        discarded_count = 0

        for sentence in sentences:
            s_clean = sentence.strip()
            # Discard short phrases or rhetorical questions
            if len(s_clean.split()) < 4 or s_clean.endswith("?"):
                continue

            # Opinion filter
            s_lower = s_clean.lower()
            if lang == "hi" and any(cue in s_clean for cue in opinion_cues_hi):
                discarded_count += 1
                continue
            elif lang == "en" and any(cue in s_lower for cue in opinion_cues_en):
                discarded_count += 1
                continue

            # Extract entities and numbers
            entities, numbers = self._extract_entities_and_numbers(s_clean, lang)

            # Classify claim type
            claim_type = ClaimType.FACTUAL
            if numbers:
                claim_type = ClaimType.NUMERICAL
            if '"' in s_clean or "“" in s_clean or "कहा" in s_clean or "said" in s_lower:
                claim_type = ClaimType.QUOTE

            # Formulate queries
            claim_id = self._generate_claim_id(s_clean)
            if lang == "hi":
                neutral_query = f"{s_clean[:120]}"
                counter_query = f"{s_clean[:100]} तथ्य जांच फर्जी खबर"
            else:
                neutral_query = f"{s_clean[:120]}"
                counter_query = f"{s_clean[:100]} fact check debunk false"

            claims.append(
                ExtractedClaim(
                    id=claim_id,
                    claim_text=s_clean,
                    claim_type=claim_type,
                    entities=entities,
                    dates_or_numbers=numbers,
                    neutral_search_query=neutral_query,
                    counter_search_query=counter_query,
                    language=lang,
                    is_verifiable=True
                )
            )

        return claims, discarded_count

    def _extract_entities_and_numbers(self, sentence: str, lang: str) -> Tuple[List[str], List[str]]:
        """Extract basic entities (capitalized phrases/acronyms) and dates/numbers."""
        numbers = re.findall(r"\b\d+(?:\.\d+)?%?|\b[०-९]+(?:\.[०-९]+)?%?", sentence)
        
        entities = []
        if lang == "en":
            # Extract capitalized words/acronyms (e.g. "Federal Reserve", "WHO", "NASA")
            caps = re.findall(r"\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\b", sentence)
            entities = [c for c in caps if len(c) > 2 and c.lower() not in {"the", "this", "that", "there"}]
        else:
            # For Hindi, look for English acronyms or terms in quotes
            english_entities = re.findall(r"\b[A-Z]{2,}\b|[A-Z][a-zA-Z0-9]+", sentence)
            quoted = re.findall(r'["\']([^"\']+)["\']', sentence)
            entities = list(set(english_entities + quoted))

        return entities[:5], numbers[:5]

    def _generate_claim_id(self, claim_text: str) -> str:
        """Deterministic unique claim identifier based on text content."""
        clean = claim_text.strip().lower()
        hash_digest = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:12]
        return f"clm_{hash_digest}"


# Global singleton instance
claim_extractor = ClaimExtractor()

