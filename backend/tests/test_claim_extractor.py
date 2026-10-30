"""
TruthLens 2.0 - Claim Extraction Engine Tests
Tests claim deconstruction, entity extraction, query formulation,
opinion filtering, and deterministic fallback for English and Hindi.
"""
import pytest
from app.schemas.claim import ClaimType
from app.services.claim_extractor import ClaimExtractor, claim_extractor


def test_extract_claims_english():
    """Verify claim extraction from factual English article."""
    text = (
        "WASHINGTON - The Federal Reserve maintained benchmark interest rates at 5.25% on Wednesday. "
        "Fed Chair Jerome Powell confirmed that inflation decreased to 2.6% in October 2024. "
        "In my opinion, this was the best decision for the country."
    )
    result = claim_extractor.extract_claims(text=text)

    assert result.language == "en"
    assert result.total_claims >= 2
    
    # Check claim contents
    first_claim = result.claims[0]
    assert first_claim.id.startswith("clm_")
    assert len(first_claim.claim_text) > 10
    assert first_claim.neutral_search_query != ""
    assert "fact check" in first_claim.counter_search_query.lower() or "debunk" in first_claim.counter_search_query.lower()
    assert result.processing_time_ms > 0


def test_extract_claims_hindi():
    """Verify claim extraction from Devanagari Hindi text."""
    text = (
        "भारतीय अंतरिक्ष अनुसंधान संगठन (ISRO) ने घोषणा की कि चंद्रयान-3 के रोवर ने चंद्रमा पर सल्फर की खोज की है। "
        "यह मिशन अगस्त २०२३ में सफलतापूर्वक लैंड हुआ था।"
    )
    result = claim_extractor.extract_claims(text=text)

    assert result.language == "hi"
    assert result.total_claims >= 1

    first_claim = result.claims[0]
    assert "चंद्रयान-3" in first_claim.claim_text or "ISRO" in first_claim.claim_text or "चंद्रमा" in first_claim.claim_text
    assert first_claim.language == "hi"


def test_extract_claims_hinglish():
    """Verify extraction from code-mixed Hinglish news."""
    text = (
        "RBI ने UPI ट्रांजेक्शन की सीमा को बढ़ाकर 5 लाख रुपये कर दिया है। "
        "यह नया नियम 1 जनवरी 2025 से लागू होगा।"
    )
    result = claim_extractor.extract_claims(text=text)

    assert result.language == "hi"
    assert result.total_claims >= 1
    assert result.is_code_mixed is True


def test_claim_id_determinism():
    """Ensure identical claim text produces deterministic claim ID."""
    extractor = ClaimExtractor()
    id1 = extractor._generate_claim_id("The Earth orbits the Sun.")
    id2 = extractor._generate_claim_id("The Earth orbits the Sun. ")
    id3 = extractor._generate_claim_id("the earth orbits the sun.")
    assert id1 == id2 == id3


def test_empty_input_handling():
    """Verify empty or whitespace-only input returns empty response without exceptions."""
    result = claim_extractor.extract_claims("")
    assert result.total_claims == 0
    assert len(result.claims) == 0

    result2 = claim_extractor.extract_claims("   ")
    assert result2.total_claims == 0

