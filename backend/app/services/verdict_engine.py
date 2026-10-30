"""
TruthLens 2.0 - Verdict Synthesis Engine
Synthesizes claim-level verdicts and overall document credibility.
Enforces strict evidence independence, detects outdated claims,
and prevents hallucinated or unverified conclusions.
"""
from datetime import datetime, timezone
import logging
from typing import List, Set
import re

from app.schemas.claim import ExtractedClaim
from app.schemas.verification import (
    ClaimVerificationResult,
    FinalVerdict,
    NLILabel,
    NLIPassageEvaluation,
)

logger = logging.getLogger("truthlens.verdict_engine")


class VerdictEngine:
    """
    Evaluates evidence independence and assigns transparent verdicts.
    """

    def synthesize_claim_verdict(
        self,
        claim: ExtractedClaim,
        evaluations: List[NLIPassageEvaluation]
    ) -> ClaimVerificationResult:
        """
        Synthesizes verdict for an individual claim based on passage evaluations.
        Enforces that syndicated copies do not count as independent confirmations.
        """
        if not evaluations:
            return ClaimVerificationResult(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type.value,
                language=claim.language,
                verdict=FinalVerdict.UNVERIFIED,
                confidence=0.50,
                supporting_evidence_count=0,
                contradicting_evidence_count=0,
                evaluations=[],
                explanation=(
                    "No verifiable evidence was found online to substantiate or refute this claim. "
                    "TruthLens marks uncorroborated assertions as UNVERIFIED rather than assuming falsehood."
                )
            )

        supporting_clusters: Set[str] = set()
        contradicting_clusters: Set[str] = set()
        oldest_pub_year = None
        newest_pub_year = None

        for ev in evaluations:
            cluster_key = ev.cluster_id or ev.source_domain

            # Extract year from published_date if available
            if ev.published_date:
                match = re.search(r"\b(19\d\d|20\d\d)\b", ev.published_date)
                if match:
                    year = int(match.group(1))
                    oldest_pub_year = min(oldest_pub_year or year, year)
                    newest_pub_year = max(newest_pub_year or year, year)

            # Syndicated copies are displayed in audit trail but don't add to cluster count
            if ev.is_syndicated:
                continue

            if ev.nli_label == NLILabel.ENTAILMENT:
                supporting_clusters.add(cluster_key)
            elif ev.nli_label == NLILabel.CONTRADICTION:
                contradicting_clusters.add(cluster_key)

        support_count = len(supporting_clusters)
        contra_count = len(contradicting_clusters)

        current_year = datetime.now(timezone.utc).year

        # Check for OUTDATED verdict: evidence is from >= 3 years ago and claim lacks date context
        is_temporally_outdated = False
        if newest_pub_year and (current_year - newest_pub_year) >= 3:
            # If claim text itself does not mention the older year
            if str(newest_pub_year) not in claim.claim_text:
                is_temporally_outdated = True

        # Assign verdict
        if is_temporally_outdated and support_count >= 1 and contra_count == 0:
            verdict = FinalVerdict.OUTDATED
            confidence = 0.85
            explanation = (
                f"This claim reflects genuine historical events originally published around {newest_pub_year}, "
                f"but lacks contemporary context and is presented misleadingly as breaking or current news."
            )
        elif support_count >= 1 and contra_count == 0:
            verdict = FinalVerdict.SUPPORTED
            confidence = round(min(0.98, 0.70 + 0.08 * support_count), 2)
            explanation = (
                f"Corroborated by {support_count} independent publisher(s) with consistent factual evidence."
            )
        elif contra_count >= 1 and support_count == 0:
            verdict = FinalVerdict.REFUTED
            confidence = round(min(0.98, 0.75 + 0.08 * contra_count), 2)
            explanation = (
                f"Directly contradicted or debunked by {contra_count} independent authoritative source(s)."
            )
        elif support_count >= 1 and contra_count >= 1:
            verdict = FinalVerdict.MIXED
            confidence = 0.80
            explanation = (
                f"Conflicting evidence found: supported by {support_count} source(s) but refuted by "
                f"{contra_count} source(s). Key contextual nuances or statistics may be disputed."
            )
        else:
            verdict = FinalVerdict.UNVERIFIED
            confidence = 0.50
            explanation = (
                "Passages retrieved discuss related subject matter but lack definitive entailment or refutation."
            )

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
            explanation=explanation
        )

    def synthesize_document_verdict(
        self,
        claim_results: List[ClaimVerificationResult]
    ) -> FinalVerdict:
        """
        Combines per-claim verdicts into a cohesive overall document verdict.
        """
        if not claim_results:
            return FinalVerdict.UNVERIFIED

        verdicts = [cr.verdict for cr in claim_results]
        total = len(verdicts)

        refuted_count = verdicts.count(FinalVerdict.REFUTED)
        supported_count = verdicts.count(FinalVerdict.SUPPORTED)
        mixed_count = verdicts.count(FinalVerdict.MIXED)
        outdated_count = verdicts.count(FinalVerdict.OUTDATED)
        unverified_count = verdicts.count(FinalVerdict.UNVERIFIED)

        # Clear unanimous cases
        if supported_count == total:
            return FinalVerdict.SUPPORTED
        if refuted_count == total:
            return FinalVerdict.REFUTED
        if unverified_count == total:
            return FinalVerdict.UNVERIFIED
        if outdated_count == total:
            return FinalVerdict.OUTDATED

        # Mixed combinations
        if refuted_count > 0 and supported_count > 0:
            return FinalVerdict.MIXED
        if mixed_count > 0:
            return FinalVerdict.MIXED
        if refuted_count > 0 and unverified_count > 0:
            return FinalVerdict.REFUTED
        if supported_count > 0 and unverified_count > 0:
            return FinalVerdict.SUPPORTED
        if outdated_count > 0:
            return FinalVerdict.OUTDATED

        return FinalVerdict.MIXED


# Global singleton
verdict_engine = VerdictEngine()

