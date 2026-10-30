"""
TruthLens 2.0 - Multilingual NLP Package
Provides language registry, script detection, and normalizers for English and Hindi.
"""
from app.nlp.registry import LanguageProfile, LanguageRegistry, language_registry
from app.nlp.normalizers import (
    BaseNormalizer,
    EnglishNormalizer,
    HindiNormalizer,
    get_normalizer,
)

__all__ = [
    "LanguageProfile",
    "LanguageRegistry",
    "language_registry",
    "BaseNormalizer",
    "EnglishNormalizer",
    "HindiNormalizer",
    "get_normalizer",
]

