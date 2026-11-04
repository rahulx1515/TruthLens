"""
TruthLens - Claim Extraction Engine
Decomposes submitted articles, headlines, or claims into atomic verifiable assertions.
Extracts entities, metrics, and formulates dual search queries (neutral & counter-hypothesis).
Supports English and Hindi natively with an Ollama LLM pipeline and robust rule-based fallback.
Optimized for fast CPU inference without prompt bloat or timeouts.
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
from app.services.llm_service import LLMService, llm_service

logger = logging.getLogger("truthlens.claim_extractor")


class ClaimExtractor:
    """
    Extracts atomic, verifiable claims from multilingual news content.
    Tracks whether LLM extraction succeeded or rule-based fallback was used.
    """

    def __init__(self, client: Optional[OllamaClient] = None, llm: Optional[LLMService] = None):
        self.ollama = client or ollama_client
        self.llm = llm or llm_service

    def extract_claims(self, text: str, headline: Optional[str] = None) -> ClaimExtractionResponse:
        """
        Main entry point for claim extraction.
        Combines headline and text, detects language, limits prompt length intelligently,
        and extracts atomic claims via LLM or rule-based fallback.
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
                processing_time_ms=0.0,
                extraction_method="rule_based",
                fallback_reason="Empty input provided"
            )

        # Step 1: Language and Script Detection
        lang, confidence, is_code_mixed = language_registry.detect_language(combined_text)
        normalizer = get_normalizer(lang)
        normalized_text = normalizer.normalize(combined_text)

        # Step 2: Extract claims via Ollama (or fallback)
        claims = []
        discarded_opinions = 0
        extraction_method = "llm"
        fallback_reason = None

        # Intelligent input limiting for CPU inference:
        # Keep input text concise (~1400 chars) to prevent Ollama CPU timeouts
        concise_text = self._compress_text_for_llm(normalized_text, normalizer, max_chars=1400)

        # Try LLM-based extraction first if any LLM provider is available
        if self.llm.is_available():
            try:
                claims, discarded_opinions = self._extract_with_llm(
                    concise_text, lang=lang, is_code_mixed=is_code_mixed
                )
                if claims:
                    extraction_method = "llm"
                else:
                    claims, discarded_opinions = self._extract_with_rules(normalized_text, lang)
                    extraction_method = "rule_based_fallback"
                    fallback_reason = "LLM returned no valid assertions; rule-based extraction applied"
            except Exception as e:
                logger.warning(f"LLM claim extraction failed ({e}), using rule-based fallback")
                claims, discarded_opinions = self._extract_with_rules(normalized_text, lang)
                extraction_method = "rule_based_fallback"
                fallback_reason = f"LLM generation failed or timed out ({type(e).__name__})"
        else:
            claims, discarded_opinions = self._extract_with_rules(normalized_text, lang)
            extraction_method = "rule_based_fallback"
            fallback_reason = "No neural LLM service configured or reachable"

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return ClaimExtractionResponse(
            language=lang,
            is_code_mixed=is_code_mixed,
            original_text=combined_text,
            claims=claims,
            total_claims=len(claims),
            discarded_opinions_count=discarded_opinions,
            processing_time_ms=elapsed_ms,
            extraction_method=extraction_method,
            fallback_reason=fallback_reason
        )

    def _compress_text_for_llm(self, text: str, normalizer, max_chars: int = 1400) -> str:
        """
        Intelligently retains the most informative sentences up to max_chars
        to avoid choking local CPU LLM inference.
        """
        if len(text) <= max_chars:
            return text

        sentences = normalizer.split_sentences(text)
        selected = []
        current_len = 0

        # Always take first 2-3 sentences as they contain the core lede
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            if current_len + len(s_clean) > max_chars and selected:
                break
            selected.append(s_clean)
            current_len += len(s_clean) + 1

        return " ".join(selected)

    def _extract_with_llm(
        self, text: str, lang: str, is_code_mixed: bool
    ) -> Tuple[List[ExtractedClaim], int]:
        """Extract claims using local Ollama model with structured JSON enforcement and CPU bounds."""
        if lang == "hi":
            system_prompt = (
                "You are an expert news verification engine for TruthLens. "
                "Extract 1 to 4 atomic, checkable factual claims from the Hindi text. "
                "Preserve authentic Devanagari Unicode. Separate facts from opinions. "
                "Output strict JSON only."
            )
            prompt = f"""Extract checkable claims from this Hindi news text:
\"\"\"{text}\"\"\"

Output strict JSON matching:
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
                "You are an expert news verification engine for TruthLens. "
                "Extract 1 to 4 atomic, checkable factual claims from the English news text. "
                "Separate verifiable statements from subjective opinions. "
                "Output strict JSON only."
            )
            prompt = f"""Extract checkable claims from this English news text:
\"\"\"{text}\"\"\"

Output strict JSON matching:
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

        data, provider = self.llm.generate_json(prompt=prompt, system=system_prompt)
        if not data:
            return [], 0
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
            elif "fact check" not in counter_q.lower() and "debunk" not in counter_q.lower() and "तथ्य" not in counter_q and "फर्जी" not in counter_q:
                counter_q = f"{counter_q} fact check debunk"

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
        discarded_opinions = 0

        for s in sentences:
            s_clean = s.strip()
            if not s_clean or len(s_clean) < 15:
                continue

            # Check opinion markers
            s_lower = s_clean.lower()
            cues = opinion_cues_hi if lang == "hi" else opinion_cues_en
            if any(cue in s_lower for cue in cues):
                discarded_opinions += 1
                continue

            # Identify numbers or dates
            has_numbers = bool(re.search(r"\b\d+([.,]\d+)?%?\b", s_clean))
            claim_type = ClaimType.NUMERICAL if has_numbers else ClaimType.FACTUAL

            # Extract basic entities
            entities = []
            if lang == "en":
                # Capitalized words that are not start of sentence
                words = s_clean.split()
                for w in words[1:]:
                    if w and w[0].isupper() and w.isalpha() and len(w) > 2:
                        entities.append(w)
            elif lang == "hi":
                # Check for known organizations or entities
                known_entities = ["इसरो", "भारत", "चंद्रयान", "नासा", "सरकार", "आरबीआई", "संसद"]
                for ke in known_entities:
                    if ke in s_clean:
                        entities.append(ke)

            claim_id = self._generate_claim_id(s_clean)

            # Build dual queries
            neutral_q = self._build_neutral_query(s_clean, lang, normalizer)
            counter_q = self._build_counter_query(s_clean, lang)

            claims.append(
                ExtractedClaim(
                    id=claim_id,
                    claim_text=s_clean,
                    claim_type=claim_type,
                    entities=entities[:4],
                    dates_or_numbers=re.findall(r"\b\d+([.,]\d+)?%?\b", s_clean)[:3],
                    neutral_search_query=neutral_q,
                    counter_search_query=counter_q,
                    language=lang,
                    is_verifiable=True
                )
            )

            # Limit to 5 claims max per article
            if len(claims) >= 5:
                break

        return claims, discarded_opinions

    def _build_neutral_query(self, sentence: str, lang: str, normalizer) -> str:
        """Strips punctuation and stop words to formulate a neutral keyword search query."""
        tokens = normalizer.tokenize(sentence)
        stop_en = {"the", "is", "in", "and", "to", "of", "a", "that", "it", "at", "by", "for", "with", "on", "are", "was"}
        stop_hi = {"है", "हैं", "के", "में", "की", "को", "और", "से", "का", "था", "नहीं", "ने", "पर", "किया", "गया", "यह", "कि"}
        stops = stop_hi if lang == "hi" else stop_en

        filtered = [t for t in tokens if t.lower() not in stops and len(t) > 1]
        query = " ".join(filtered[:8])
        return query or sentence[:60]

    def _build_counter_query(self, sentence: str, lang: str) -> str:
        """Formulates counter-hypothesis query targeted at fact-check and debunk coverage."""
        if lang == "hi":
            return f"{sentence[:50]} तथ्य जांच फर्जी दावा"
        return f"{sentence[:50]} fact check false debunk"

    def _generate_claim_id(self, text: str) -> str:
        """Deterministic claim ID derived from normalized lower text content."""
        digest = hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:10]
        return f"clm_{digest}"


# Global singleton
claim_extractor = ClaimExtractor()
