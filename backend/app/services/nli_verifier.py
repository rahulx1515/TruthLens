"""
TruthLens - Multilingual NLI Claim Verifier
Performs Natural Language Inference (NLI) between retrieved evidence passages (premise)
and atomic claims (hypothesis).
Supports multilingual entailment and contradiction scoring on CPU with calibrated thresholds.
Distinguishes neural transformer inference, Hugging Face Inference API, and calibrated heuristic fallback.
Avoids importing PyTorch at application startup when local neural NLI is disabled.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.schemas.evidence import EvidencePassage
from app.schemas.verification import NLILabel, NLIPassageEvaluation
from app.services.evidence_collector import classify_source_type

logger = logging.getLogger("truthlens.nli")


class NLIVerifier:
    """
    Multilingual NLI Verifier.
    Supports:
    1. Local CPU PyTorch transformer (MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli) when ENABLE_LOCAL_NEURAL_NLI=True
    2. Remote Hugging Face Inference API when configured with HF_API_KEY / HUGGINGFACE_API_KEY
    3. Calibrated deterministic multilingual heuristic fallback
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        entailment_threshold: Optional[float] = None,
        contradiction_threshold: Optional[float] = None
    ):
        self.model_name = model_name or settings.NLI_MODEL_NAME
        self.entailment_threshold = entailment_threshold or settings.NLI_ENTAILMENT_THRESHOLD
        self.contradiction_threshold = contradiction_threshold or settings.NLI_CONTRADICTION_THRESHOLD
        
        self.tokenizer = None
        self.model = None
        self.device = "cpu"
        self._is_loaded = False
        self._load_attempted = False
        self._load_error: Optional[str] = None

    @property
    def is_neural_available(self) -> bool:
        """Returns True if the PyTorch Hugging Face transformer model is in memory."""
        return self._is_loaded and self.model is not None and self.tokenizer is not None

    @property
    def is_hf_api_configured(self) -> bool:
        """Returns True if Hugging Face API key or custom endpoint is configured for remote NLI."""
        return bool(settings.HF_API_KEY or settings.HUGGINGFACE_API_KEY or settings.HF_API_URL)

    def load_model(self) -> bool:
        """
        Loads Hugging Face NLI transformer model into memory on CPU once if enabled.
        Does not import PyTorch or Transformers when ENABLE_LOCAL_NEURAL_NLI is False.
        """
        if not getattr(settings, "ENABLE_LOCAL_NEURAL_NLI", False):
            logger.info("Local neural NLI is disabled (ENABLE_LOCAL_NEURAL_NLI=false); skipping local transformer load.")
            return False

        if self._is_loaded:
            return True
        if self._load_attempted and not self._is_loaded:
            # Do not repeatedly try and fail across every request
            return False

        self._load_attempted = True
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            torch.set_num_threads(settings.OLLAMA_NUM_THREADS)

            logger.info(f"Loading local NLI model {self.model_name} on CPU...")
            start_t = time.time()
            try:
                # Prefer local cache to prevent network timeout retries
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, local_files_only=True)
            except Exception:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=False)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, local_files_only=False)
            self.model.to(self.device)
            self.model.eval()
            self._is_loaded = True
            load_duration = round(time.time() - start_t, 2)
            logger.info(f"NLI model successfully loaded in {load_duration}s.")
            return True
        except Exception as e:
            self._load_error = str(e)
            logger.warning(
                f"Could not load Hugging Face NLI model ({e}). "
                f"Activating deterministic multilingual NLI fallback."
            )
            self._is_loaded = False
            return False

    def evaluate_passage(
        self,
        claim_text: str,
        passage: EvidencePassage,
        lang: str = "en"
    ) -> NLIPassageEvaluation:
        """
        Evaluates relationship between evidence passage (premise) and claim (hypothesis).
        Tracks whether local neural, remote HF API, or heuristic fallback was applied.
        Never reports 'hf_inference_api' or 'neural' unless that method actually succeeded.
        """
        entail_p: Optional[float] = None
        contra_p: Optional[float] = None
        neutral_p: Optional[float] = None
        inference_method = "heuristic_fallback"

        # 1. Local neural transformer inference if loaded
        if self.is_neural_available:
            try:
                entail_p, contra_p, neutral_p = self._predict_neural(
                    premise=passage.passage_text, hypothesis=claim_text
                )
                inference_method = "neural"
            except Exception as e:
                logger.warning(f"Local neural NLI prediction failed: {e}")
                entail_p = contra_p = neutral_p = None

        # 2. Remote Hugging Face Inference API if configured
        if entail_p is None and self.is_hf_api_configured:
            try:
                hf_scores = self._predict_hf_api(
                    premise=passage.passage_text, hypothesis=claim_text
                )
                if hf_scores is not None:
                    entail_p, contra_p, neutral_p = hf_scores
                    inference_method = "hf_inference_api"
            except Exception as e:
                logger.warning(f"Hugging Face NLI inference failed: {e}")
                entail_p = contra_p = neutral_p = None

        # 3. Deterministic lexical and semantic heuristic fallback
        if entail_p is None or contra_p is None or neutral_p is None:
            entail_p, contra_p, neutral_p = self._predict_heuristic(
                premise=passage.passage_text, hypothesis=claim_text, lang=lang
            )
            inference_method = "heuristic_fallback"

        # Apply calibrated decision thresholds
        if entail_p >= self.entailment_threshold and entail_p > contra_p:
            winning_label = NLILabel.ENTAILMENT
            relation_explanation = (
                "Passage directly confirms or entails the claim assertion with strong evidence."
            )
        elif contra_p >= self.contradiction_threshold and contra_p > entail_p:
            winning_label = NLILabel.CONTRADICTION
            relation_explanation = (
                "Passage directly contradicts or debunks the factual assertion."
            )
        else:
            winning_label = NLILabel.NEUTRAL
            relation_explanation = (
                "Passage discusses related context but neither confirms nor contradicts the assertion."
            )

        source_type = classify_source_type(passage.canonical_domain)

        return NLIPassageEvaluation(
            passage_id=passage.passage_id,
            article_url=passage.article_url,
            article_title=passage.article_title,
            source_domain=passage.canonical_domain,
            publisher_name=passage.publisher_name,
            quoted_passage=passage.passage_text,
            published_date=passage.published_date,
            retrieved_at=passage.retrieved_at,
            nli_label=winning_label,
            entailment_prob=round(entail_p, 4),
            contradiction_prob=round(contra_p, 4),
            neutral_prob=round(neutral_p, 4),
            inference_method=inference_method,
            relevance_score=passage.relevance_score,
            exact_quotation_verified=True,
            source_type=source_type,
            relation_explanation=relation_explanation,
            is_syndicated=passage.is_syndicated_copy,
            cluster_id=passage.cluster_id
        )

    def _predict_neural(self, premise: str, hypothesis: str) -> Tuple[float, float, float]:
        """Runs PyTorch sequence classification on CPU."""
        import torch
        with torch.no_grad():
            inputs = self.tokenizer(
                premise,
                hypothesis,
                truncation=True,
                max_length=256,
                return_tensors="pt"
            ).to(self.device)

            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=1).squeeze().tolist()

            # Handle label mappings (entailment, neutral, contradiction)
            id2label = {idx: label.lower() for idx, label in self.model.config.id2label.items()}
            entail_idx = next(i for i, l in id2label.items() if "entail" in l)
            contra_idx = next(i for i, l in id2label.items() if "contra" in l)
            neutral_idx = next(i for i, l in id2label.items() if "neutral" in l)

            return float(probs[entail_idx]), float(probs[contra_idx]), float(probs[neutral_idx])

    def _predict_hf_api(self, premise: str, hypothesis: str) -> Optional[Tuple[float, float, float]]:
        """
        Sends a valid premise-hypothesis Natural Language Inference request to Hugging Face Inference API.
        Includes both the evidence passage (premise) and the claim (hypothesis).
        Maps the remote response to (entailment_prob, contradiction_prob, neutral_prob).
        Safely handles timeouts, HTTP errors (401, 429, 503), and non-standard payloads.
        Returns None on any error so caller explicitly uses heuristic fallback.
        """
        api_key = settings.HF_API_KEY or settings.HUGGINGFACE_API_KEY
        endpoint = settings.HF_API_URL or f"https://api-inference.huggingface.co/models/{self.model_name}"

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "inputs": {
                "text": premise,
                "text_pair": hypothesis
            },
            "parameters": {
                "wait_for_model": False
            }
        }

        try:
            import requests
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)

            # If provider rejected text_pair format, retry with standard separator string
            if resp.status_code == 400:
                alt_payload = {
                    "inputs": f"{premise} </s></s> {hypothesis}"
                }
                resp = requests.post(endpoint, json=alt_payload, headers=headers, timeout=10)

            if resp.status_code == 503:
                logger.warning("HF NLI model is currently loading on Hugging Face (503).")
                return None
            elif resp.status_code == 429:
                logger.warning("HF NLI API rate limit exceeded (429).")
                return None
            elif resp.status_code != 200:
                logger.warning(f"HF NLI API returned HTTP {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json()
            return self._parse_hf_response(data)
        except Exception as e:
            logger.warning(f"Error calling Hugging Face NLI API ({e}). Falling back to heuristic.")
            return None

    def _parse_hf_response(self, data: Any) -> Optional[Tuple[float, float, float]]:
        """Parses HF text classification response and extracts (entail_p, contra_p, neutral_p)."""
        if not isinstance(data, list) or not data:
            if isinstance(data, dict) and "error" in data:
                logger.warning(f"HF API returned error: {data['error']}")
            return None

        # Handle nested list [[{label, score}, ...]] or single [{label, score}, ...]
        items = data[0] if isinstance(data[0], list) else data
        if not isinstance(items, list):
            return None

        scores: Dict[str, float] = {}
        for item in items:
            if isinstance(item, dict) and "label" in item and "score" in item:
                lbl = str(item["label"]).strip().lower()
                try:
                    scores[lbl] = float(item["score"])
                except (ValueError, TypeError):
                    continue

        if not scores:
            return None

        entail_p = next((v for k, v in scores.items() if "entail" in k), None)
        contra_p = next((v for k, v in scores.items() if "contra" in k), None)
        neutral_p = next((v for k, v in scores.items() if "neutral" in k), None)

        # Handle unmapped labels (e.g. label_0, label_1, label_2)
        # For MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli: 0: entailment, 1: neutral, 2: contradiction
        if entail_p is None and "label_0" in scores:
            entail_p = scores.get("label_0", 0.0)
            neutral_p = scores.get("label_1", 0.0)
            contra_p = scores.get("label_2", 0.0)

        if entail_p is None or contra_p is None or neutral_p is None:
            logger.warning(f"Incomplete NLI labels returned from HF API: {list(scores.keys())}")
            return None

        total = entail_p + contra_p + neutral_p
        if total > 0:
            return (entail_p / total, contra_p / total, neutral_p / total)
        return None

    def _predict_heuristic(
        self, premise: str, hypothesis: str, lang: str = "en"
    ) -> Tuple[float, float, float]:
        """
        Deterministic lexical/semantic NLI heuristic when transformer model is offline.
        Detects agreement, contradiction cues, and topic overlap without claiming neural predictions.
        """
        import re
        p_lower = premise.lower()
        h_lower = hypothesis.lower()

        # Check for negation/contradiction signals
        contra_cues_en = {
            "not true", "false", "hoax", "debunk", "debunks", "debunked",
            "incorrect", "denied", "denies", "refuted", "refute", "refutes",
            "fake", "misleading", "untrue", "no evidence", "unfounded", "fabricated", "myth"
        }
        contra_cues_hi = {
            "फर्जी", "गलत", "खारिज", "अफवाह", "झूठ", "झूठी", "झूठे",
            "सच नहीं", "भ्रामक", "दावा गलत", "कोई आधार नहीं", "निराधार"
        }

        cues = contra_cues_hi if lang == "hi" else contra_cues_en
        has_contra_cue = any(cue in p_lower for cue in cues)

        # Tokenize cleanly without punctuation
        from app.nlp.normalizers import get_normalizer
        normalizer = get_normalizer(lang)

        def clean_token(t: str) -> str:
            t = re.sub(r"[^\w\s]", "", t).strip()
            if lang == "en":
                t = re.sub(r"(ations|ation|tions|tion|sions|sion|ing|ed|es|s|ly|ment|ments)$", "", t)
            return t

        h_tokens = [clean_token(t.lower()) for t in normalizer.tokenize(hypothesis)]
        h_tokens = [t for t in h_tokens if len(t) > 1]
        p_tokens = [clean_token(t.lower()) for t in normalizer.tokenize(premise)]
        p_tokens = [t for t in p_tokens if len(t) > 1]

        stop_en = {"the", "is", "in", "and", "to", "of", "a", "that", "it", "at", "by", "for", "with", "on", "are", "was", "an"}
        stop_hi = {"है", "हैं", "के", "में", "की", "को", "और", "से", "का", "था", "नहीं", "ने", "पर", "किया", "गया", "यह", "कि"}
        stops = stop_hi if lang == "hi" else stop_en

        h_words = {w for w in h_tokens if w not in stops and len(w) > 1}
        p_words = {w for w in p_tokens if w not in stops and len(w) > 1}

        if not h_words:
            return 0.1, 0.1, 0.8

        overlap = len(h_words.intersection(p_words)) / len(h_words)

        if overlap >= 0.20 and has_contra_cue:
            return 0.05, 0.90, 0.05
        elif overlap >= 0.30 and not has_contra_cue:
            return 0.90, 0.05, 0.05
        elif overlap >= 0.18:
            return 0.20, 0.15, 0.65
        else:
            return 0.05, 0.05, 0.90


# Global singleton
nli_verifier = NLIVerifier()
