"""
TruthLens 2.0 - Multilingual NLI Claim Verifier
Performs Natural Language Inference (NLI) between retrieved evidence passages (premise)
and atomic claims (hypothesis).
Supports multilingual entailment and contradiction scoring on CPU with calibrated thresholds.
"""
import logging
from typing import Dict, List, Optional, Tuple
import torch

from app.core.config import settings
from app.schemas.evidence import EvidencePassage
from app.schemas.verification import NLILabel, NLIPassageEvaluation

logger = logging.getLogger("truthlens.nli")


class NLIVerifier:
    """
    Multilingual NLI Verifier running on CPU with bounded resources.
    Uses MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli or deterministic fallback.
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

    def load_model(self) -> bool:
        """Loads Hugging Face NLI transformer model into memory on CPU."""
        if self._is_loaded:
            return True

        try:
            torch.set_num_threads(settings.OLLAMA_NUM_THREADS)
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            logger.info(f"Loading NLI model {self.model_name} on CPU...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self._is_loaded = True
            logger.info("NLI model successfully loaded.")
            return True
        except Exception as e:
            logger.warning(f"Could not load Hugging Face NLI model ({e}). Using deterministic NLI fallback.")
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
        """
        # If model is loaded, run neural inference
        if self._is_loaded and self.model and self.tokenizer:
            entail_p, contra_p, neutral_p = self._predict_neural(
                premise=passage.passage_text, hypothesis=claim_text
            )
        else:
            # Deterministic lexical and semantic heuristic fallback
            entail_p, contra_p, neutral_p = self._predict_heuristic(
                premise=passage.passage_text, hypothesis=claim_text, lang=lang
            )

        # Apply calibrated decision thresholds
        if entail_p >= self.entailment_threshold and entail_p > contra_p:
            winning_label = NLILabel.ENTAILMENT
        elif contra_p >= self.contradiction_threshold and contra_p > entail_p:
            winning_label = NLILabel.CONTRADICTION
        else:
            winning_label = NLILabel.NEUTRAL

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
            is_syndicated=passage.is_syndicated_copy,
            cluster_id=passage.cluster_id
        )

    def _predict_neural(self, premise: str, hypothesis: str) -> Tuple[float, float, float]:
        """Runs PyTorch sequence classification on CPU."""
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

    def _predict_heuristic(
        self, premise: str, hypothesis: str, lang: str = "en"
    ) -> Tuple[float, float, float]:
        """
        Deterministic lexical/semantic NLI heuristic when transformer model is offline.
        Detects agreement, contradiction cues, and topic overlap.
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
            # Strip punctuation and dandas
            t = re.sub(r"[^\w\s]", "", t).strip()
            if lang == "en":
                # Stem common English inflectional/derivational suffixes
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
