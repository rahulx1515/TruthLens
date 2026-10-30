"""
TruthLens 2.0 - NLI, Verdict Synthesis & Report Generator Tests
Tests NLI entailment/contradiction evaluation, syndication-aware verdict synthesis,
outdated detection, and unverified fallback without false refutations.
"""
import pytest
from app.schemas.claim import ClaimType, ExtractedClaim
from app.schemas.evidence import EvidencePassage
from app.schemas.verification import (
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
    CRITICAL: Verify that when NO evidence is found, claim verdict is UNVERIFIED,
    NEVER REFUTED.
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


def test_verdict_engine_syndication_does_not_inflate_support():
    """
    CRITICAL: Verify syndicated copies do not artificially inflate the count
    of independent supporting publishers.
    """
    claim = ExtractedClaim(
        id="c1",
        claim_text="Government announced 50,000 subsidy on electric vehicles.",
        claim_type=ClaimType.NUMERICAL,
        neutral_search_query="ev subsidy 50000",
        counter_search_query="ev subsidy 50000 fact check",
        language="en"
    )

    # 3 passages, but 2 are syndicated copies of the same wire story (cluster_1)
    ev1 = NLIPassageEvaluation(
        passage_id="p1",
        article_url="https://timesofindia.com/ev",
        source_domain="timesofindia.com",
        publisher_name="Times of India",
        quoted_passage="Government announced 50,000 subsidy on electric vehicles.",
        retrieved_at="2026-10-30T10:00:00Z",
        nli_label=NLILabel.ENTAILMENT,
        entailment_prob=0.90,
        is_syndicated=False,
        cluster_id="cluster_1"
    )
    ev2 = NLIPassageEvaluation(
        passage_id="p2",
        article_url="https://hindustantimes.com/ev",
        source_domain="hindustantimes.com",
        publisher_name="Hindustan Times",
        quoted_passage="Government announced 50,000 subsidy on electric vehicles.",
        retrieved_at="2026-10-30T10:00:00Z",
        nli_label=NLILabel.ENTAILMENT,
        entailment_prob=0.90,
        is_syndicated=True,  # syndicated wire copy
        cluster_id="cluster_1"
    )

    res = verdict_engine.synthesize_claim_verdict(claim, [ev1, ev2])
    assert res.verdict == FinalVerdict.SUPPORTED
    # MUST BE 1 independent source, NOT 2!
    assert res.supporting_evidence_count == 1


def test_verdict_engine_outdated_detection():
    """Verify claim from 2020 presented without date context is classified as OUTDATED."""
    claim = ExtractedClaim(
        id="c1",
        claim_text="Massive earthquake strikes near Tokyo.",
        claim_type=ClaimType.FACTUAL,
        neutral_search_query="tokyo earthquake",
        counter_search_query="tokyo earthquake fact check",
        language="en"
    )
    ev = NLIPassageEvaluation(
        passage_id="p1",
        article_url="https://reuters.com/tokyo-quake-2020",
        source_domain="reuters.com",
        publisher_name="Reuters",
        quoted_passage="Massive earthquake strikes near Tokyo.",
        published_date="2020-03-15",  # Over 5 years ago
        retrieved_at="2026-10-30T10:00:00Z",
        nli_label=NLILabel.ENTAILMENT,
        entailment_prob=0.88
    )
    res = verdict_engine.synthesize_claim_verdict(claim, [ev])
    assert res.verdict == FinalVerdict.OUTDATED
    assert "historical" in res.explanation.lower() or "context" in res.explanation.lower()


def test_report_generator_synthesis():
    """Verify ReportGenerator compiles complete audit trail and document verdict."""
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
        search_providers_used=["searxng", "rss"]
    )

    assert report.verification_id.startswith("rpt_")
    assert report.overall_verdict == FinalVerdict.SUPPORTED
    assert report.claims_supported == 1
    assert report.claims_total == 1
    assert len(report.executive_summary) > 30
    assert report.search_providers_used == ["searxng", "rss"]

