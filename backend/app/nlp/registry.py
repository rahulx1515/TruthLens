"""
TruthLens 2.0 - Multilingual NLP Registry
Central language configuration registry supporting English (en) and Hindi (hi),
extensible for Bengali (bn), Marathi (mr), Spanish (es), French (fr), etc.
"""
from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class LanguageProfile:
    """Configuration profile for a supported language."""
    code: str
    name: str
    native_name: str
    script: str
    sentence_delimiters: Tuple[str, ...]
    char_ranges: Tuple[Tuple[int, int], ...]
    stopword_sample: Set[str] = field(default_factory=set)
    is_officially_supported: bool = True

    def matches_char(self, char: str) -> bool:
        """Check if a single character falls into this language's primary unicode range."""
        cp = ord(char)
        return any(start <= cp <= end for start, end in self.char_ranges)


class LanguageRegistry:
    """
    Central registry for language configurations and language detection.
    """
    def __init__(self):
        self._profiles: Dict[str, LanguageProfile] = {}
        self._register_default_profiles()

    def _register_default_profiles(self):
        # 1. English (Latin script)
        self.register(LanguageProfile(
            code="en",
            name="English",
            native_name="English",
            script="Latn",
            sentence_delimiters=(".", "?", "!", "\n"),
            char_ranges=((0x0041, 0x005A), (0x0061, 0x007A)),  # A-Z, a-z
            stopword_sample={"the", "is", "in", "and", "to", "of", "a", "that", "it"},
            is_officially_supported=True
        ))

        # 2. Hindi (Devanagari script)
        # Unicode range 0x0900-0x097F covers Devanagari letters, signs, matras, virama, and danda
        self.register(LanguageProfile(
            code="hi",
            name="Hindi",
            native_name="हिन्दी",
            script="Deva",
            sentence_delimiters=("।", "॥", "?", "!", "\n", "."),
            char_ranges=((0x0900, 0x097F),),  # Devanagari
            stopword_sample={"है", "के", "में", "की", "को", "और", "से", "का", "था", "नहीं"},
            is_officially_supported=True
        ))

        # Extensible placeholders for future roadmap languages (marked unsupported initially)
        self.register(LanguageProfile(
            code="bn",
            name="Bengali",
            native_name="বাংলা",
            script="Beng",
            sentence_delimiters=("।", "?", "!", "\n"),
            char_ranges=((0x0980, 0x09FF),),
            is_officially_supported=False
        ))

        self.register(LanguageProfile(
            code="mr",
            name="Marathi",
            native_name="मराठी",
            script="Deva",
            sentence_delimiters=("।", "?", "!", "\n"),
            char_ranges=((0x0900, 0x097F),),
            is_officially_supported=False
        ))

        self.register(LanguageProfile(
            code="es",
            name="Spanish",
            native_name="Español",
            script="Latn",
            sentence_delimiters=(".", "?", "!", "¿", "¡", "\n"),
            char_ranges=((0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x00FF)),
            is_officially_supported=False
        ))

        self.register(LanguageProfile(
            code="fr",
            name="French",
            native_name="Français",
            script="Latn",
            sentence_delimiters=(".", "?", "!", "\n"),
            char_ranges=((0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x00FF)),
            is_officially_supported=False
        ))

    def register(self, profile: LanguageProfile) -> None:
        """Register or override a language profile."""
        self._profiles[profile.code.lower()] = profile

    def get(self, code: str) -> Optional[LanguageProfile]:
        """Retrieve a language profile by ISO code."""
        return self._profiles.get(code.lower())

    def is_supported(self, code: str) -> bool:
        """Check if language is currently officially supported for evidence verification."""
        profile = self.get(code)
        return bool(profile and profile.is_officially_supported)

    def list_supported_languages(self) -> List[LanguageProfile]:
        """List all officially supported languages."""
        return [p for p in self._profiles.values() if p.is_officially_supported]

    def detect_language(self, text: str) -> Tuple[str, float, bool]:
        """
        Robust script-based language identification with code-mixing (Hinglish) detection.
        
        Returns:
            Tuple[str, float, bool]: (language_code, confidence, is_code_mixed)
            - language_code: "hi" or "en" (defaults to "en" if ambiguous)
            - confidence: confidence score between 0.0 and 1.0
            - is_code_mixed: True if significant mixture of Devanagari and Latin characters exists
        """
        if not text or not text.strip():
            return "en", 1.0, False

        devanagari_count = 0
        latin_count = 0
        total_letters = 0

        for ch in text:
            cp = ord(ch)
            if 0x0900 <= cp <= 0x097F:
                devanagari_count += 1
                total_letters += 1
            elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
                latin_count += 1
                total_letters += 1

        if total_letters == 0:
            return "en", 0.5, False

        dev_ratio = devanagari_count / total_letters
        lat_ratio = latin_count / total_letters

        # Code-mixing detection: presence of both scripts in noticeable quantities
        # e.g. Indian news or tech articles with Hindi text + English acronyms/brands (e.g. RBI, UPI, WHO, AI)
        is_code_mixed = (devanagari_count >= 5 and latin_count >= 3 and 
                         min(dev_ratio, lat_ratio) >= 0.04)

        # If Devanagari is >= 20% of letters or dominant non-Latin script, classify as Hindi
        if dev_ratio >= 0.20 or devanagari_count > latin_count:
            confidence = min(0.99, max(0.60, dev_ratio))
            return "hi", confidence, is_code_mixed
        
        confidence = min(0.99, max(0.60, lat_ratio))
        return "en", confidence, is_code_mixed


# Global singleton instance
language_registry = LanguageRegistry()
