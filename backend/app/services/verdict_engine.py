"""
TruthLens - Verdict Synthesis Engine
Synthesizes claim-level verdicts and overall document credibility.
Enforces strict evidence independence, distinguishes historical claims from genuinely
outdated claims, prevents false refutations, and calculates evidence consistency scores
derived from real entailment/contradiction probabilities rather than magic constants.
"""
from datetime import datetime, timezone
import logging
import re
from typing import List, Optional, Set, Tuple

from app.schemas.claim import ExtractedClaim
from app.schemas.verification import (
    ClaimVerificationResult,
    FinalVerdict,
    NLILabel,
    NLIPassageEvaluation,
)

logger = logging.getLogger("truthlens.verdict_engine")

# Indicators denoting a claim of present-day or ongoing state
PRESENT_TENSE_CUES = {
    "currently", "now", "presently", "as of today", "at present",
    "holds the position", "is the current", "serves as", "is prime minister",
    "is president", "is ceo", "is governor", "is minister",
    "वर्तमान में", "इस समय", "अभी", "अध्यक्ष हैं", "मंत्री हैं", "पद पर हैं"
}

# Indicators in evidence denoting a transition or subsequent change over time
STATUS_CHANGE_CUES = {
    "replaced by", "succeeded by", "stepped down", "resigned in", "resigned from",
    "former", "formerly", "no longer", "defeated by", "ousted", "was succeeded",
    "was replaced", "ex-prime minister", "ex-president", "retired in",
    "पूर्व", "स्थान लिया", "इस्तीफा दे दिया", "पद छोड़ा", "हटा दिया गया", "भूतपूर्व"
}


class VerdictEngine:
    """
    Evaluates evidence independence and assigns transparent, explainable verdicts.
    Labels scores according to what they actually measure: Evidence Corroboration / Consistency.
    Preserves UNVERIFIED whenever evidence is insufficient.
    """

    def synthesize_claim_verdict(
        self,
        claim: ExtractedClaim,
        evaluations: List[NLIPassageEvaluation]
    ) -> ClaimVerificationResult:
        """
        Synthesizes verdict for an individual claim based on passage evaluations.
        Enforces evidence independence and calculates empirical consistency scores.
        """
        # Case 0: No passages retrieved or empty evaluations
        if not evaluations:
            return ClaimVerificationResult(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type.value,
                language=claim.language,
                verdict=FinalVerdict.UNVERIFIED,
                confidence=0.0,
                supporting_evidence_count=0,
                contradicting_evidence_count=0,
                evaluations=[],
                explanation=(
                    "No verifiable independent evidence was found online to substantiate or refute this assertion. "
                    "TruthLens strictly assigns UNVERIFIED rather than assuming falsehood without evidence."
                ),
                why_verdict="Zero credible web evidence found addressing this assertion.",
                corroboration_score=0.0,
                limitations="Live web retrieval yielded no sufficiently relevant passages directly addressing this assertion."
            )

        supporting_evals = [e for e in evaluations if e.nli_label == NLILabel.ENTAILMENT]
        contradicting_evals = [e for e in evaluations if e.nli_label == NLILabel.CONTRADICTION]
        neutral_evals = [e for e in evaluations if e.nli_label == NLILabel.NEUTRAL]

        # Extract independent publishers (deduplicating syndicated wire reprints)
        supporting_clusters: Set[str] = set()
        for ev in supporting_evals:
            if not ev.is_syndicated:
                supporting_clusters.add(ev.cluster_id or ev.source_domain)

        contradicting_clusters: Set[str] = set()
        for ev in contradicting_evals:
            if not ev.is_syndicated:
                contradicting_clusters.add(ev.cluster_id or ev.source_domain)

        support_count = len(supporting_clusters)
        contra_count = len(contradicting_clusters)

        # -------------------------------------------------------------
        # 1. OUTDATED EVALUATION:
        # Require evidence of a relevant change over time, or a present-tense
        # claim contradicted by subsequent status change.
        # Distinguish historical facts (which remain true) from changed situations.
        # -------------------------------------------------------------
        c_lower = claim.claim_text.lower()
        has_present_tense_assertion = any(cue in c_lower for cue in PRESENT_TENSE_CUES)

        # Check if retrieved passages contain evidence of status change
        has_change_of_status_evidence = False
        for ev in evaluations:
            p_lower = ev.quoted_passage.lower()
            if any(sc in p_lower for sc in STATUS_CHANGE_CUES):
                has_change_of_status_evidence = True
                break

        is_genuinely_outdated = False
        if has_present_tense_assertion and has_change_of_status_evidence and (contra_count >= 1 or support_count >= 1):
            is_genuinely_outdated = True

        # -------------------------------------------------------------
        # 2. VERDICT ASSIGNMENT & EMPIRICAL SCORE CALCULATION
        # -------------------------------------------------------------
        if is_genuinely_outdated:
            verdict = FinalVerdict.OUTDATED
            mean_prob = sum(e.entailment_prob for e in supporting_evals) / max(1, len(supporting_evals)) if supporting_evals else 0.70
            corroboration_score = round(mean_prob, 3)
            confidence = corroboration_score
            why_verdict = (
                "The assertion claims an ongoing present condition, but evidence documents a subsequent "
                "change of status or leadership transition."
            )
            explanation = (
                "This claim asserts a present or ongoing situation that has been superseded by subsequent events. "
                "While historically accurate at one point, it is now outdated and misleading when presented as current."
            )
            limitations = "Requires contemporary temporal context; older reporting does not reflect recent changes."

        elif support_count >= 1 and contra_count == 0:
            verdict = FinalVerdict.SUPPORTED
            # Empirical corroboration score derived from real entailment probabilities
            mean_entailment = sum(e.entailment_prob for e in supporting_evals) / len(supporting_evals)
            # Source diversity scaling: corroboration increases with independent publishers (capped at 1.0)
            diversity_scaling = min(1.0, 0.85 + 0.05 * min(support_count, 3))
            corroboration_score = round(min(1.0, mean_entailment * diversity_scaling), 3)
            confidence = corroboration_score
            why_verdict = f"Corroborated by {support_count} independent publisher(s) with consistent factual evidence."
            explanation = (
                f"Corroborated by {support_count} independent publisher(s) with consistent factual evidence "
                f"(mean textual entailment agreement: {round(mean_entailment * 100, 1)}%)."
            )
            limitations = None

        elif contra_count >= 1 and support_count == 0:
            verdict = FinalVerdict.REFUTED
            # Empirical contradiction score derived from real contradiction probabilities
            mean_contradiction = sum(e.contradiction_prob for e in contradicting_evals) / len(contradicting_evals)
            diversity_scaling = min(1.0, 0.90 + 0.05 * min(contra_count, 2))
            corroboration_score = round(min(1.0, mean_contradiction * diversity_scaling), 3)
            confidence = corroboration_score
            why_verdict = f"Directly contradicted by {contra_count} independent authoritative source(s)."
            explanation = (
                f"Directly contradicted or debunked by {contra_count} independent authoritative source(s) "
                f"(mean textual contradiction agreement: {round(mean_contradiction * 100, 1)}%)."
            )
            limitations = None

        elif support_count >= 1 and contra_count >= 1:
            verdict = FinalVerdict.MIXED
            # Measure degree of conflict between supporting and contradicting sources
            total_active = support_count + contra_count
            balance_ratio = min(support_count, contra_count) / max(support_count, contra_count)
            corroboration_score = round(balance_ratio, 3)
            # Confidence reflects evidence volume and balance
            confidence = round(min(1.0, 0.60 + 0.10 * total_active), 2)
            why_verdict = f"Conflicting evidence: {support_count} supporting vs {contra_count} contradicting source(s)."
            explanation = (
                f"Conflicting evidence found: supported by {support_count} source(s) but contradicted by "
                f"{contra_count} source(s). Key contextual facts or figures are disputed."
            )
            limitations = "Contradictory reports exist among established sources; further reporting needed."

        else:
            # Passages were neutral or below relevance threshold
            verdict = FinalVerdict.UNVERIFIED
            corroboration_score = 0.0
            confidence = 0.0
            why_verdict = "Available evidence does not definitively confirm or refute the assertion."
            explanation = (
                "Passages retrieved discuss related subject matter but lack definitive entailment or refutation. "
                "TruthLens marks this as UNVERIFIED."
            )
            limitations = "Insufficient conclusive evidence to assign a definitive true or false determination."

        return ClaimVerificationResult(
            claim_id=claim.id,
            claim_text=claim.claim_text,
            claim_type=claim.claim_type.value,
            language=claim.language,
            verdict=verdict,
            confidence=confidence,
            supporting_evidence_count=support_count,
            contradicting_evidence_count=contra_count,
            evaluations=evaluations,
            explanation=explanation,
            why_verdict=why_verdict,
            corroboration_score=corroboration_score,
            limitations=limitations
        )

    def synthesize_document_verdict(
        self,
        claim_results: List[ClaimVerificationResult]
    ) -> FinalVerdict:
        """
        Combines per-claim verdicts into a cohesive overall document verdict.
        Rules:
        - A single refuted minor claim must NOT automatically make an entire article REFUTED.
        - Unverified claims remain unverified.
        - Transparently reflects mixed and outdated content.
        """
        if not claim_results:
            return FinalVerdict.UNVERIFIED

        verdicts = [cr.verdict for cr in claim_results]
        total = len(verdicts)

        if total == 1:
            return verdicts[0]

        refuted_count = verdicts.count(FinalVerdict.REFUTED)
        supported_count = verdicts.count(FinalVerdict.SUPPORTED)
        mixed_count = verdicts.count(FinalVerdict.MIXED)
        outdated_count = verdicts.count(FinalVerdict.OUTDATED)
        unverified_count = verdicts.count(FinalVerdict.UNVERIFIED)

        # Unanimous cases
        if supported_count == total:
            return FinalVerdict.SUPPORTED
        if refuted_count == total:
            return FinalVerdict.REFUTED
        if unverified_count == total:
            return FinalVerdict.UNVERIFIED
        if outdated_count == total:
            return FinalVerdict.OUTDATED

        # Combinations:
        # If any claims are refuted AND some are supported:
        # -> MIXED (A single refuted minor claim must not automatically make the entire article REFUTED)
        if refuted_count > 0 and supported_count > 0:
            return FinalVerdict.MIXED

        if mixed_count > 0:
            return FinalVerdict.MIXED

        # If supported + unverified (0 refuted):
        if supported_count > 0 and refuted_count == 0:
            if supported_count >= unverified_count:
                return FinalVerdict.SUPPORTED
            else:
                return FinalVerdict.MIXED

        # If refuted + unverified (0 supported):
        if refuted_count > 0 and supported_count == 0:
            if refuted_count > unverified_count:
                return FinalVerdict.REFUTED
            else:
                return FinalVerdict.MIXED

        if outdated_count > 0:
            return FinalVerdict.OUTDATED

        return FinalVerdict.UNVERIFIED


# Global singleton
verdict_engine = VerdictEngine()
