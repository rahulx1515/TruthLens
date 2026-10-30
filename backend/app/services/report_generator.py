"""
TruthLens 2.0 - Report Synthesis Generator
Synthesizes comprehensive verification reports with transparent audit trails,
exact extracted quotations, distinct publication/retrieval dates, and verified clickable URLs.
"""
from datetime import datetime, timezone
import logging
from typing import List, Optional
import uuid

from app.ml.ollama_client import OllamaClient, ollama_client
from app.schemas.verification import (
    ClaimVerificationResult,
    FinalVerdict,
    VerificationReport,
)
from app.services.verdict_engine import verdict_engine

logger = logging.getLogger("truthlens.report_generator")


class ReportGenerator:
    """
    Generates transparent, evidence-based verification reports.
    """

    def __init__(self, client: Optional[OllamaClient] = None):
        self.ollama = client or ollama_client

    def generate_report(
        self,
        original_content: str,
        original_title: Optional[str],
        detected_language: str,
        is_code_mixed: bool,
        claim_results: List[ClaimVerificationResult],
        search_providers_used: List[str]
    ) -> VerificationReport:
        """
        Synthesizes the complete VerificationReport.
        """
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Compute document-level verdict
        overall_verdict = verdict_engine.synthesize_document_verdict(claim_results)

        # Count claims by verdict
        claims_total = len(claim_results)
        claims_supported = sum(1 for c in claim_results if c.verdict == FinalVerdict.SUPPORTED)
        claims_refuted = sum(1 for c in claim_results if c.verdict == FinalVerdict.REFUTED)
        claims_unverified = sum(1 for c in claim_results if c.verdict == FinalVerdict.UNVERIFIED)
        claims_outdated = sum(1 for c in claim_results if c.verdict == FinalVerdict.OUTDATED)

        # Compute overall confidence
        if claim_results:
            overall_confidence = round(sum(c.confidence for c in claim_results) / len(claim_results), 2)
        else:
            overall_confidence = 0.50

        # Synthesize executive summary
        summary = self._synthesize_summary(
            original_content=original_content,
            headline=original_title,
            overall_verdict=overall_verdict,
            claim_results=claim_results,
            lang=detected_language
        )

        return VerificationReport(
            verification_id=report_id,
            original_title=original_title,
            original_content=original_content,
            detected_language=detected_language,
            is_code_mixed=is_code_mixed,
            overall_verdict=overall_verdict,
            overall_confidence=overall_confidence,
            executive_summary=summary,
            claims_total=claims_total,
            claims_supported=claims_supported,
            claims_refuted=claims_refuted,
            claims_unverified=claims_unverified,
            claims_outdated=claims_outdated,
            claim_results=claim_results,
            search_providers_used=search_providers_used,
            created_at=now_iso
        )

    def _synthesize_summary(
        self,
        original_content: str,
        headline: Optional[str],
        overall_verdict: FinalVerdict,
        claim_results: List[ClaimVerificationResult],
        lang: str = "en"
    ) -> str:
        """Synthesize human-readable summary with Ollama or fallback template."""
        if self.ollama.is_healthy():
            try:
                system_prompt = (
                    "You are the senior editorial verifier for TruthLens 2.0. "
                    "Write a concise, objective 2-paragraph executive verification summary. "
                    "Never invent quotes or URLs. Reference the verified evidence findings directly."
                )
                findings_summary = "\n".join(
                    f"- Claim: \"{c.claim_text}\" -> Verdict: {c.verdict.value} ({c.explanation})"
                    for c in claim_results
                )
                prompt = (
                    f"Headline: {headline or 'N/A'}\n"
                    f"Language: {lang}\n"
                    f"Final Verdict: {overall_verdict.value}\n\n"
                    f"Investigated Claim Findings:\n{findings_summary}\n\n"
                    f"Provide a clear, balanced factual summary explaining why this verdict was reached."
                )
                resp = self.ollama.generate(prompt=prompt, system=system_prompt)
                generated_text = resp.get("response", "").strip()
                if generated_text and len(generated_text) > 30:
                    return generated_text
            except Exception as e:
                logger.info(f"Ollama summary synthesis failed ({e}), using template")

        # Deterministic template fallback
        return self._template_summary(overall_verdict, claim_results, lang)

    def _template_summary(
        self, verdict: FinalVerdict, claim_results: List[ClaimVerificationResult], lang: str
    ) -> str:
        """High-clarity deterministic summary template."""
        supported_claims = [c for c in claim_results if c.verdict == FinalVerdict.SUPPORTED]
        refuted_claims = [c for c in claim_results if c.verdict == FinalVerdict.REFUTED]
        unverified_claims = [c for c in claim_results if c.verdict == FinalVerdict.UNVERIFIED]
        outdated_claims = [c for c in claim_results if c.verdict == FinalVerdict.OUTDATED]

        if lang == "hi":
            if verdict == FinalVerdict.SUPPORTED:
                return (
                    f"TruthLens सत्यापन के अनुसार, प्रस्तुत समाचार के मुख्य दावे स्वतंत्र और विश्वसनीय स्रोतों द्वारा समर्थित हैं। "
                    f"कुल {len(claim_results)} दावों की जांच की गई, जिसमें {len(supported_claims)} दावे सत्यापित पाए गए।"
                )
            elif verdict == FinalVerdict.REFUTED:
                return (
                    f"TruthLens सत्यापन के अनुसार, प्रस्तुत सामग्री में किए गए दावे विश्वसनीय तथ्यों और आधिकारिक रिपोर्टों के विपरीत पाए गए हैं। "
                    f"मुख्य दावों का खंडन आधिकारिक स्रोतों द्वारा किया गया है।"
                )
            elif verdict == FinalVerdict.MIXED:
                return (
                    f"प्रस्तुत समाचार में आंशिक सत्यता और भ्रामक जानकारी का मिश्रण पाया गया है। "
                    f"कुछ दावे समर्थित हैं जबकि अन्य दावों में अतिशयोक्ति या तथ्यहीनता देखी गई।"
                )
            elif verdict == FinalVerdict.OUTDATED:
                return (
                    f"जांच में पाया गया कि यह घटना पुरानी है और इसे वर्तमान संदर्भ के बिना भ्रामक तरीके से प्रस्तुत किया गया है।"
                )
            else:
                return (
                    f"प्रस्तुत दावों के समर्थन या खंडन के लिए इंटरनेट पर पर्याप्त स्वतंत्र साक्ष्य नहीं मिले। "
                    f"TruthLens इसे असत्यापित (UNVERIFIED) के रूप में वर्गीकृत करता है।"
                )

        # English
        if verdict == FinalVerdict.SUPPORTED:
            return (
                f"TruthLens investigated {len(claim_results)} factual assertion(s). Core claims were corroborated "
                f"by independent publishers with consistent primary reporting and verified evidence."
            )
        elif verdict == FinalVerdict.REFUTED:
            return (
                f"TruthLens investigated {len(claim_results)} factual assertion(s). Core claims were directly contradicted "
                f"or debunked by authoritative sources and official records."
            )
        elif verdict == FinalVerdict.MIXED:
            return (
                f"TruthLens found a mixture of factual truth and misleading elements across {len(claim_results)} assertion(s). "
                f"{len(supported_claims)} claim(s) were supported while {len(refuted_claims)} were refuted or exaggerated."
            )
        elif verdict == FinalVerdict.OUTDATED:
            return (
                f"The claims correspond to genuine historical events, but lack temporal context and are being circulated "
                f"misleadingly as breaking or contemporary news."
            )
        else:
            return (
                f"Insufficient independent evidence was located online to definitively substantiate or refute these claims. "
                f"TruthLens marks uncorroborated assertions as UNVERIFIED rather than presuming falsehood without evidence."
            )


# Global singleton
report_generator = ReportGenerator()

