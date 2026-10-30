"""
TruthLens 2.0 - Multilingual NLP Unit Tests
Tests language registry, script detection, and English/Hindi normalizers.
Specifically verifies Devanagari matras, virama, danda sentence splitting,
and entity/number preservation.
"""
import pytest
from app.nlp.registry import LanguageRegistry, language_registry
from app.nlp.normalizers import (
    EnglishNormalizer,
    HindiNormalizer,
    get_normalizer,
)


# ==============================================================================
# LANGUAGE REGISTRY & SCRIPT DETECTION TESTS
# ==============================================================================

def test_language_registry_supported_profiles():
    """Verify officially supported languages and future roadmap placeholders."""
    assert language_registry.is_supported("en") is True
    assert language_registry.is_supported("hi") is True
    assert language_registry.is_supported("bn") is False
    assert language_registry.is_supported("es") is False

    supported = [p.code for p in language_registry.list_supported_languages()]
    assert "en" in supported
    assert "hi" in supported
    assert len(supported) == 2


def test_script_detection_english():
    """Verify detection of English text."""
    text = "The Federal Reserve raised interest rates by 25 basis points on Wednesday."
    lang, conf, is_mixed = language_registry.detect_language(text)
    assert lang == "en"
    assert conf >= 0.80
    assert is_mixed is False


def test_script_detection_hindi():
    """Verify detection of pure Devanagari Hindi text."""
    text = "भारतीय रिज़र्व बैंक ने रेपो दर में कोई बदलाव नहीं करने का फैसला किया है।"
    lang, conf, is_mixed = language_registry.detect_language(text)
    assert lang == "hi"
    assert conf >= 0.85
    assert is_mixed is False


def test_script_detection_hinglish_code_mixed():
    """Verify detection of code-mixed Hindi text with English entities."""
    text = "WHO ने COVID-19 वैक्सीन को लेकर नई गाइडलाइन जारी की है।"
    lang, conf, is_mixed = language_registry.detect_language(text)
    assert lang == "hi"
    assert is_mixed is True


# ==============================================================================
# ENGLISH NORMALIZER TESTS
# ==============================================================================

def test_english_normalizer_contractions():
    """Verify contraction expansion without destroying text semantics."""
    normalizer = EnglishNormalizer()
    text = "It's claimed the minister won't sign the treaty and can't attend."
    normalized = normalizer.normalize(text)
    assert "it is" in normalized.lower()
    assert "will not" in normalized.lower()
    assert "cannot" in normalized.lower()


def test_english_normalizer_entity_and_date_preservation():
    """Ensure dates, numbers, currency, and entities are never stripped."""
    normalizer = EnglishNormalizer()
    raw = '“The U.S. economy grew by 3.2% in Q3 2024, adding $150M in value,” said Dr. Smith.'
    normalized = normalizer.normalize(raw)

    assert "3.2%" in normalized
    assert "$150M" in normalized
    assert "Q3 2024" in normalized
    assert "Dr. Smith" in normalized
    assert '"' in normalized  # curly quote normalized to straight quote


def test_english_normalizer_sentence_splitting():
    """Ensure sentence splitting respects abbreviations and numeric decimals."""
    normalizer = EnglishNormalizer()
    text = (
        "The U.S. military budget was approved yesterday. Dr. Adams presented $4.5B in findings. "
        "Will the bill pass in the Senate? The vote is scheduled for tomorrow!"
    )
    sentences = normalizer.split_sentences(text)
    assert len(sentences) == 4
    assert sentences[0] == "The U.S. military budget was approved yesterday."
    assert sentences[1] == "Dr. Adams presented $4.5B in findings."
    assert sentences[2] == "Will the bill pass in the Senate?"
    assert sentences[3] == "The vote is scheduled for tomorrow!"


def test_english_normalizer_tokenization():
    """Verify tokenization preserves hyphenated terms and alphanumeric tokens."""
    normalizer = EnglishNormalizer()
    tokens = normalizer.tokenize("COVID-19 vaccine clinical-trial results for 2024.")
    assert "COVID-19" in tokens
    assert "clinical-trial" in tokens
    assert "2024" in tokens


# ==============================================================================
# HINDI NORMALIZER TESTS
# ==============================================================================

def test_hindi_normalizer_matras_and_virama_preservation():
    """
    CRITICAL: Verify Devanagari matras, virama (halant), and conjuncts are never corrupted.
    """
    normalizer = HindiNormalizer()
    # Contains:
    # Virama/halant: क्या (क + ् + य), दिल्ली (ल + ् + ल)
    # Matras: ू (उ), ी (ई), ो (ओ), े (ए), ौ (औ)
    # Anusvara: सं (ं), केंद्र
    text = "क्या दिल्ली और केंद्र सरकार के बीच नया समझौता हुआ है?"
    normalized = normalizer.normalize(text)

    assert "क्या" in normalized
    assert "दिल्ली" in normalized
    assert "केंद्र" in normalized
    assert "समझौता" in normalized


def test_hindi_normalizer_danda_sentence_splitting():
    """
    Verify sentence splitting on danda (।), double danda (॥), and punctuation,
    while protecting Hindi abbreviations and decimal numbers.
    """
    normalizer = HindiNormalizer()
    text = (
        "डॉ. शर्मा ने १०.५ प्रतिशत विकास दर का अनुमान लगाया। "
        "यह रिपोर्ट कल संसद में पेश की जाएगी। क्या यह सच है?"
    )
    sentences = normalizer.split_sentences(text)

    assert len(sentences) == 3
    assert sentences[0].startswith("डॉ. शर्मा")
    assert "१०.५" in sentences[0]
    assert sentences[1] == "यह रिपोर्ट कल संसद में पेश की जाएगी।"
    assert sentences[2] == "क्या यह सच है?"


def test_hindi_normalizer_digit_conversion():
    """Verify optional Devanagari digit conversion to Western numerals."""
    normalizer = HindiNormalizer()
    text = "वर्ष २०२४ में कुल ५० प्रतिशत काम पूरा हुआ।"
    converted = normalizer.normalize(text, convert_digits=True)
    assert "2024" in converted
    assert "50" in converted
    assert "वर्ष" in converted


def test_hindi_normalizer_code_mixed_hinglish():
    """Verify mixed Hindi and English text maintains integrity of both scripts."""
    normalizer = HindiNormalizer()
    text = "ISRO ने Chandrayaan-3 मिशन की सफलता पर 100% पुष्टि की।"
    normalized = normalizer.normalize(text)

    assert "ISRO" in normalized
    assert "Chandrayaan-3" in normalized
    assert "सफलता" in normalized
    assert "100%" in normalized
    assert "पुष्टि" in normalized


def test_get_normalizer_factory():
    """Verify normalizer factory instantiation."""
    en_norm = get_normalizer("en")
    assert isinstance(en_norm, EnglishNormalizer)

    hi_norm = get_normalizer("hi")
    assert isinstance(hi_norm, HindiNormalizer)

    # Defaults to English for unknown languages
    default_norm = get_normalizer("xx")
    assert isinstance(default_norm, EnglishNormalizer)

