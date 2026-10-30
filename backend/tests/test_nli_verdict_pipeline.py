"""
TruthLens - NLI, Verdict Synthesis & Report Generator Tests
Tests NLI entailment/contradiction evaluation, syndication-aware verdict synthesis,
distinguishing historical claims from genuinely outdated claims, and unverified fallback without false refutations.
"""
import pytest
from app.schemas.claim import ClaimType, ExtractedClaim
from app.schemas.evidence import EvidencePassage
from app.schemas.verification import (
    ClaimVerificationResult,
    FinalVerdict,
    NLILabel,
    NLIPassageEvaluation,
)
from app.services.nli_verifier import NLIVerifier, nli_verifier
from app.services.report_generator import report_generator
from app.services.verdict_engine import verdict_engine


def test_nli_heuristic_evaluation_english():
    """Verify NLI evaluation detects entailment and contradiction in English."""
    verifier = NLIVerifier()

    claim = "The Federal Reserve raised interest rates."
    supporting_passage = EvidencePassage(
        passage_id="p1",
        article_url="https://reuters.com/rates",
        canonical_domain="reuters.com",
        publisher_name="Reuters",
        passage_text="The Federal Reserve announced it raised interest rates by 25 basis points.",
        retrieved_at="2026-10-30T10:00:00Z"
    )
    ev_sup = verifier.evaluate_passage(claim, supporting_passage, lang="en")
    assert ev_sup.nli_label == NLILabel.ENTAILMENT
    assert ev_sup.entailment_prob >= 0.65
    assert ev_sup.inference_method in ("neural", "heuristic_fallback")

    debunk_passage = EvidencePassage(
        passage_id="p2",
        article_url="https://apnews.com/factcheck",
        canonical_domain="apnews.com",
        publisher_name="Apnews",
        passage_text="Claims that the Federal Reserve raised interest rates are false and debunked.",
        retrieved_at="2026-10-30T10:00:00Z"
    )
    ev_debunk = verifier.evaluate_passage(claim, debunk_passage, lang="en")
    assert ev_debunk.nli_label == NLILabel.CONTRADICTION
    assert ev_debunk.contradiction_prob >= 0.65


def test_nli_heuristic_evaluation_hindi():
    """Verify NLI evaluation detects Hindi agreement and refutation cues."""
    verifier = NLIVerifier()

    claim = "चंद्रयान-3 ने चंद्रमा पर सल्फर की खोज की।"
    sup_passage = EvidencePassage(
        passage_id="p1",
        article_url="https://bbc.com/hindi/chandrayaan",
        canonical_domain="bbc.com",
        publisher_name="Bbc",
        passage_text="ISRO ने पुष्टि की कि चंद्रयान-3 ने चंद्रमा पर सल्फर की खोज की है।",
        retrieved_at="2026-10-30T10:00:00Z"
    )
    ev = verifier.evaluate_passage(claim, sup_passage, lang="hi")
    assert ev.nli_label == NLILabel.ENTAILMENT

    debunk_passage = EvidencePassage(
        passage_id="p2",
        article_url="https://factcheck.in/fake",
        canonical_domain="factcheck.in",
        publisher_name="Factcheck",
        passage_text="यह दावा कि चंद्रयान-3 ने सल्फर की खोज की पूरी तरह फर्जी और गलत है।",
        retrieved_at="2026-10-30T10:00:00Z"
    )
    ev_debunk = verifier.evaluate_passage(claim, debunk_passage, lang="hi")
    assert ev_debunk.nli_label == NLILabel.CONTRADICTION


def test_verdict_engine_unverified_fallback():
    """
    CRITICAL: Verify that when NO evidence is found, claim verdict is UNVERIFIED with confidence 0.0,
    NEVER REFUTED, and never hardcoded to 0.50.
    """
    claim = ExtractedClaim(
        id="c1",
        claim_text="An ancient underwater city was discovered near Antarctica.",
        claim_type=ClaimType.FACTUAL,
        neutral_search_query="antarctica underwater city",
        counter_search_query="antarctica underwater city fact check",
        language="en"
    )
    res = verdict_engine.synthesize_claim_verdict(claim, evaluations=[])
    assert res.verdict == FinalVerdict.UNVERIFIED
    assert res.supporting_evidence_count == 0
    assert res.contradicting_evidence_count == 0
    assert "UNVERIFIED" in res.explanation
    assert res.confidence == 0.0
    assert res.corroboration_score == 0.0


def test_verdict_engine_syndication_does_not_inflate_support():
    """
    CRITICAL: Verify syndicated copies do not artificially inflate the count
    of independent supporting publishers.
    """
    claim = ExtractedClaim(
        id="c1",
        claim_text="Government issues electric vehicle guidelines.",
        claim_type=ClaimType.FACTUAL,
        neutral_search_query="ev guidelines",
        counter_search_query="ev guidelines fact check",
        language="en"
    )
    ev1 = NLIPassageEvaluation(
        passage_id="p1",
        article_url="https://reuters.com/ev",
        source_domain="reuters.com",
        publisher_name="Reuters",
        quoted_passage="Government issues electric vehicle guidelines.",
        retrieved_at="2026-10-30T10:00:00Z",
        nli_label=NLILabel.ENTAILMENT,
        entailment_prob=0.90,
        is_syndicated=False
    )
    ev2 = NLIPassageEvaluation(
        passage_id="p2",
        article_url="https://timesofindia.com/ev",
        source_domain="timesofindia.com",
        publisher_name="Timesofindia",
        quoted_passage="Government issues electric vehicle guidelines.",
        retrieved_at="2026-10-30T10:00:00Z",
        nli_label=NLILabel.ENTAILMENT,
        entailment_prob=0.90,
        is_syndicated=True,  # Wire copy
        cluster_id="cluster_pti"
    )
    res = verdict_engine.synthesize_claim_verdict(claim, [ev1, ev2])
    assert res.verdict == FinalVerdict.SUPPORTED
    assert res.supporting_evidence_count == 1  # Only 1 independent cluster counted


def test_historical_claim_not_misclassified_as_outdated():
    """
    CRITICAL (Section 5): Historical facts from years ago without change of status
    must remain SUPPORTED, and NOT be inferred as OUTDATED solely due to source age.
    """
    historical_claim = ExtractedClaim(
        id="c_hist",
        claim_text="In 1969 Neil Armstrong became the first person to walk on the Moon.",
        claim_type=ClaimType.FACTUAL,
        neutral_search_query="Neil Armstrong moon 1969",
        counter_search_query="Neil Armstrong moon 1969 debunk",
        language="en"
    )
    ev = NLIPassageEvaluation(
        passage_id="p_hist",
        article_url="https://nasa.gov/apollo11",
        source_domain="nasa.gov",
        publisher_name="NASA",
        quoted_passage="Neil Armstrong stepped onto the lunar surface on July 20, 1969.",
        published_date="2019-07-20",  # Published > 3 years ago
        retrieved_at="2026-10-30T10:00:00Z",
        nli_label=NLILabel.ENTAILMENT,
        entailment_prob=0.95
    )
    res = verdict_engine.synthesize_claim_verdict(historical_claim, [ev])
    assert res.verdict == FinalVerdict.SUPPORTED
    assert res.verdict != FinalVerdict.OUTDATED


def test_verdict_engine_genuine_outdated_detection():
    """
    CRITICAL (Section 5): A claim asserting ongoing present state (e.g. 'currently serves as')
    contradicted by subsequent evidence showing status change is classified as OUTDATED.
    """
    outdated_claim = ExtractedClaim(
        id="c_outdated",
        claim_text="Boris Johnson currently serves as Prime Minister of the United Kingdom.",
        claim_type=ClaimType.FACTUAL,
        neutral_search_query="Boris Johnson currently Prime Minister UK",
        counter_search_query="Boris Johnson Prime Minister UK status",
        language="en"
    )
    ev_transition = NLIPassageEvaluation(
        passage_id="p_trans",
        article_url="https://bbc.com/boris-resigns",
        source_domain="bbc.com",
        publisher_name="BBC",
        quoted_passage="Boris Johnson announced he stepped down and resigned from his post, succeeded by Liz Truss.",
        published_date="2022-09-06",
        retrieved_at="2026-10-30T10:00:00Z",
        nli_label=NLILabel.CONTRADICTION,
        contradiction_prob=0.92
    )
    res = verdict_engine.synthesize_claim_verdict(outdated_claim, [ev_transition])
    assert res.verdict == FinalVerdict.OUTDATED
    assert "superseded" in res.explanation.lower() or "outdated" in res.explanation.lower()


def test_minor_refuted_claim_yields_mixed_article_not_refuted():
    """
    CRITICAL REGRESSION TEST (Section 9):
    A single refuted minor claim must NOT automatically make an entire article REFUTED.
    When 2 claims are supported and 1 minor claim is refuted, the article verdict is MIXED.
    """
    c1 = ClaimVerificationResult(
        claim_id="c1",
        claim_text="NASA successfully lands rover on Mars.",
        claim_type="factual",
        language="en",
        verdict=FinalVerdict.SUPPORTED,
        confidence=0.90,
        supporting_evidence_count=2,
        contradicting_evidence_count=0
    )
    c2 = ClaimVerificationResult(
        claim_id="c2",
        claim_text="The rover collected rock samples from Jezero crater.",
        claim_type="factual",
        language="en",
        verdict=FinalVerdict.SUPPORTED,
        confidence=0.88,
        supporting_evidence_count=2,
        contradicting_evidence_count=0
    )
    c3_minor_refuted = ClaimVerificationResult(
        claim_id="c3",
        claim_text="The mission discovered living alien microbes on the surface.",
        claim_type="factual",
        language="en",
        verdict=FinalVerdict.REFUTED,
        confidence=0.92,
        supporting_evidence_count=0,
        contradicting_evidence_count=2
    )

    doc_verdict = verdict_engine.synthesize_document_verdict([c1, c2, c3_minor_refuted])
    assert doc_verdict == FinalVerdict.MIXED
    assert doc_verdict != FinalVerdict.REFUTED


def test_report_generator_synthesis_with_why_verdict():
    """Verify ReportGenerator compiles complete audit trail, why_this_verdict, and document verdict."""
    claim = ExtractedClaim(
        id="c1",
        claim_text="ISRO launched Aditya-L1 solar mission.",
        claim_type=ClaimType.FACTUAL,
        neutral_search_query="aditya-l1 isro solar mission",
        counter_search_query="aditya-l1 isro fact check",
        language="en"
    )
    ev = NLIPassageEvaluation(
        passage_id="p1",
        article_url="https://pib.gov.in/aditya-l1",
        source_domain="pib.gov.in",
        publisher_name="PIB India",
        quoted_passage="ISRO successfully launched Aditya-L1 solar mission.",
        retrieved_at="2026-10-30T10:00:00Z",
        nli_label=NLILabel.ENTAILMENT,
        entailment_prob=0.92
    )
    claim_res = verdict_engine.synthesize_claim_verdict(claim, [ev])

    report = report_generator.generate_report(
        original_content="ISRO launched Aditya-L1 solar mission to study the Sun.",
        original_title="India Launches Solar Probe",
        detected_language="en",
        is_code_mixed=False,
        claim_results=[claim_res],
        search_providers_used=["searxng", "rss"],
        extraction_method="llm",
        nli_inference_method="heuristic_fallback"
    )

    assert report.verification_id.startswith("rpt_")
    assert report.overall_verdict == FinalVerdict.SUPPORTED
    assert report.claims_supported == 1
    assert report.claims_total == 1
    assert len(report.executive_summary) > 30
    assert report.why_this_verdict is not None
    assert report.limitations_and_uncertainty is not None
    assert report.extraction_method == "llm"
    assert report.nli_inference_method == "heuristic_fallback"
