"""
TruthLens 2.0 - Evidence Chunking & Syndication Tests
Tests URL canonicalization, passage chunking, BM25 scoring, and wire-service syndication detection.
"""
import pytest
from app.schemas.claim import ExtractedClaim, ClaimType
from app.schemas.evidence import EvidencePassage
from app.services.evidence_deduplicator import EvidenceDeduplicator, evidence_deduplicator
from app.services.passage_chunker import PassageChunker, passage_chunker
from rank_bm25 import BM25Plus


def test_url_canonicalization():
    """Verify tracking parameters and hash fragments are cleanly stripped."""
    dedup = EvidenceDeduplicator()
    dirty_url = "https://www.Reuters.com/article/world-news-2024/?utm_source=twitter&utm_medium=social&fbclid=123456#main-content"
    clean = dedup.canonicalize_url(dirty_url)
    assert clean == "https://reuters.com/article/world-news-2024"

    dirty_url2 = "http://ndtv.com/india-news/report?ref=home&session_id=abc987/"
    clean2 = dedup.canonicalize_url(dirty_url2)
    assert "ref" not in clean2
    assert "session_id" not in clean2
    assert not clean2.endswith("/")


def test_passage_chunker_basic():
    """Verify passage chunker segments article into coherent passages with exact text preserved."""
    chunker = PassageChunker(target_words=30, overlap_sentences=1)
    article = (
        "The Federal Reserve announced an unexpected pause on interest rates yesterday. "
        "Economic analysts had forecasted a 25 basis point hike in borrowing costs. "
        "However, recent employment and consumer price inflation figures influenced the committee's decision. "
        "Global stock markets rallied shortly following the official statement. "
        "Investors viewed the monetary pause as an encouraging sign of economic stabilization."
    )
    chunks = chunker.chunk_article(article, lang="en")
    assert len(chunks) >= 2
    for pid, text, wcount in chunks:
        assert pid.startswith("psg_")
        assert len(text) > 30
        assert wcount >= 15
        # Verify text is exact verbatim substring of article
        for sent in text.split(". "):
            if sent.strip():
                assert sent.strip() in article


def test_passage_chunker_hindi():
    """Verify Hindi passage chunking preserves Devanagari sentences and danda."""
    chunker = PassageChunker(target_words=20, overlap_sentences=1)
    article = (
        "भारतीय अंतरिक्ष अनुसंधान संगठन (ISRO) ने आज एक ऐतिहासिक मिशन पूरा किया। "
        "चंद्रयान-3 मिशन के सभी वैज्ञानिक उपकरण पूरी तरह से सक्रिय हैं। "
        "वैज्ञानिकों ने चंद्रमा के दक्षिणी ध्रुव पर महत्वपूर्ण खनिजों का विश्लेषण किया है। "
        "यह उपलब्धि भारत को अंतरिक्ष अन्वेषण में वैश्विक स्तर पर अग्रणी बनाती है।"
    )
    chunks = chunker.chunk_article(article, lang="hi")
    assert len(chunks) >= 1
    assert "ISRO" in chunks[0][1]
    assert "चंद्रयान-3" in chunks[0][1]


def test_syndication_detection_wire_service():
    """
    CRITICAL: Verify near-identical wire copy republished across different domains
    is clustered and marked as syndicated, not counted as separate independent sources.
    """
    dedup = EvidenceDeduplicator(jaccard_threshold=0.60)

    # Identical PTI wire story published by two different outlets
    wire_text = (
        "NEW DELHI (PTI) - The government on Monday notified the new electric vehicle subsidy policy. "
        "The scheme will offer direct subsidies of up to 50,000 rupees for two-wheelers and provides "
        "comprehensive incentives for charging infrastructure across major national highways."
    )
    
    # Completely distinct editorial analysis from another outlet
    distinct_text = (
        "Automotive market analysts report mixed consumer sentiment regarding public battery swapping networks. "
        "High initial costs and slow urban grid modernization present challenges for rural adoption."
    )

    p1 = EvidencePassage(
        passage_id="p1",
        article_url="https://timesofindia.indiatimes.com/auto/news1",
        canonical_domain="timesofindia.indiatimes.com",
        publisher_name="Timesofindia",
        passage_text=wire_text
    )
    p2 = EvidencePassage(
        passage_id="p2",
        article_url="https://hindustantimes.com/auto/news1",
        canonical_domain="hindustantimes.com",
        publisher_name="Hindustantimes",
        passage_text=wire_text  # identical wire copy
    )
    p3 = EvidencePassage(
        passage_id="p3",
        article_url="https://bbc.com/news/business-ev-analysis",
        canonical_domain="bbc.com",
        publisher_name="Bbc",
        passage_text=distinct_text  # independent source
    )

    passages, indep_count, synd_count = dedup.detect_syndication([p1, p2, p3])

    assert indep_count == 2  # Only 2 independent stories, NOT 3
    assert synd_count == 1   # Exactly 1 syndicated copy detected

    # p2 should be marked as syndicated copy of p1
    assert p1.is_syndicated_copy is False
    assert p2.is_syndicated_copy is True
    assert p2.primary_source_url == p1.article_url
    assert p3.is_syndicated_copy is False


def test_bm25_lexical_scoring():
    """Verify BM25 scores relevant passage higher than irrelevant passage."""
    corpus = [
        "The Federal Reserve held benchmark interest rates steady at 5.25 percent.",
        "A rare species of sea turtle was discovered nesting on a tropical island beach."
    ]
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Plus(tokenized_corpus)

    query = "Federal Reserve interest rates".lower().split()
    scores = bm25.get_scores(query)

    assert scores[0] > scores[1]
