"""
TruthLens 2.0 - Multilingual Text Normalizers
Provides specialized normalizers for English and Hindi text verification.
Preserves entities, numbers, dates, punctuation semantics, and Devanagari Unicode
without destructive stripping.
"""
from abc import ABC, abstractmethod
import re
import unicodedata
from typing import List, Optional, Set


class BaseNormalizer(ABC):
    """Abstract interface for language-specific text normalizers."""

    @abstractmethod
    def normalize(self, text: str) -> str:
        """Clean and normalize text while preserving semantic entities."""
        pass

    @abstractmethod
    def split_sentences(self, text: str) -> List[str]:
        """Split text into individual checkable sentences."""
        pass

    @abstractmethod
    def tokenize(self, text: str) -> List[str]:
        """Split text into lexical tokens."""
        pass


class EnglishNormalizer(BaseNormalizer):
    """
    Normalizer for English news text.
    Preserves numbers, dates, currency, percentages, and entities.
    Expands common contractions and splits sentences without breaking on abbreviations.
    """

    # Common English contractions mapping
    CONTRACTIONS = {
        r"\bcan't\b": "cannot",
        r"\bwon't\b": "will not",
        r"\bshan't\b": "shall not",
        r"\bn't\b": " not",
        r"\bi'm\b": "i am",
        r"\b(it|he|she|that|there|what)'s\b": r"\1 is",
        r"\b're\b": " are",
        r"\b've\b": " have",
        r"\b'll\b": " will",
        r"\b'd\b": " would",
    }

    # Common abbreviations to prevent sentence splitting
    ABBREVIATIONS = (
        r"u\.s\.", r"u\.k\.", r"u\.n\.", r"e\.u\.", r"d\.c\.",
        r"dr\.", r"mr\.", r"mrs\.", r"ms\.", r"prof\.", r"gov\.", r"sen\.", r"rep\.",
        r"inc\.", r"corp\.", r"ltd\.", r"co\.", r"dept\.",
        r"jan\.", r"feb\.", r"mar\.", r"apr\.", r"jun\.", r"jul\.", r"aug\.", r"sep\.", r"sept\.", r"oct\.", r"nov\.", r"dec\.",
        r"vs\.", r"e\.g\.", r"i\.e\.", r"etc\.", r"approx\.", r"a\.m\.", r"p\.m\.", r"no\."
    )

    def normalize(self, text: str) -> str:
        """
        Normalizes English text:
        - Unicode normalization (NFC)
        - Normalizes curly quotes and dashes
        - Expands contractions (case-insensitively)
        - Normalizes irregular whitespace while keeping semantic punctuation
        """
        if not text:
            return ""

        # Canonical Unicode normalization
        text = unicodedata.normalize("NFC", str(text))

        # Standardize quotes and hyphens
        text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
        text = text.replace("—", " - ").replace("–", " - ")

        # Expand contractions
        for pattern, replacement in self.CONTRACTIONS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Collapse excess whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
        return text

    def split_sentences(self, text: str) -> List[str]:
        """
        Splits English text into sentences while respecting abbreviations, decimals, and URLs.
        """
        if not text or not text.strip():
            return []

        clean = self.normalize(text)

        # Protect known abbreviations by replacing internal dots with a placeholder
        placeholder = "@@DOT@@"
        protected = clean
        for abbr in self.ABBREVIATIONS:
            def repl(match):
                return match.group(0).replace(".", placeholder)
            protected = re.sub(r"(?i)\b" + abbr, repl, protected)

        # Protect numbers with decimals (e.g. 3.14 or 12.5%)
        protected = re.sub(r"(\d)\.(\d)", rf"\1{placeholder}\2", protected)

        # Sentence split on '.', '?', '!', followed by whitespace or line break
        raw_sentences = re.split(r"(?<=[.?!])\s+", protected)

        # Restore dots and filter empty strings
        sentences = []
        for s in raw_sentences:
            restored = s.replace(placeholder, ".").strip()
            if restored:
                sentences.append(restored)

        return sentences

    def tokenize(self, text: str) -> List[str]:
        """Lexical tokenization preserving words, numbers, and contractions."""
        if not text:
            return []
        norm = self.normalize(text)
        # Tokenize by word characters, hyphenated compounds, and punctuation
        return re.findall(r"\b\w+(?:[-']\w+)*\b|[^\w\s]", norm)


class HindiNormalizer(BaseNormalizer):
    """
    Normalizer for Hindi and Hinglish news text.
    Preserves:
    - Devanagari Unicode range 0x0900-0x097F (matras, virama, halant, anusvara, visarga, danda)
    - Code-mixed English entities and numbers
    - Sentence boundaries with Hindi danda (।) and double danda (॥)
    - Normalizes Unicode canonical representation (NFC)
    """

    # Devanagari to Western digit conversion map
    DEVA_TO_WEST_DIGITS = {
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
        '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
    }

    # Hindi honorifics and abbreviations that should not break sentences
    HINDI_ABBREVIATIONS = (
        r"डॉ\.", r"पं\.", r"प्रो\.", r"श्री\.", r"श्रीमती\.", r"सुश्री\.", r"क्र\.", r"सं\."
    )

    def normalize(self, text: str, convert_digits: bool = False) -> str:
        """
        Normalizes Hindi and Hinglish text:
        - Unicode normalization (NFC) ensuring combining matras and viramas stay attached
        - Preserves all Devanagari vowel signs (matras) and halant
        - Standardizes danda and punctuation spacing
        - Optionally maps Devanagari numerals (०-९) to Western digits (0-9)
        """
        if not text:
            return ""

        # NFC normalization combines detached combining marks with base consonants
        text = unicodedata.normalize("NFC", str(text))

        # Standardize quotes and punctuation
        text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
        text = text.replace("—", " - ").replace("–", " - ")

        # Ensure danda (।) has a trailing space if followed by text without space
        text = re.sub(r"।(?=[^\s॥\n])", "। ", text)
        text = re.sub(r"॥(?=[^\s\n])", "॥ ", text)

        # Optional conversion of Devanagari digits to standard digits
        if convert_digits:
            for deva_digit, west_digit in self.DEVA_TO_WEST_DIGITS.items():
                text = text.replace(deva_digit, west_digit)

        # Normalize redundant spaces while preserving sentence structure
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
        return text

    def split_sentences(self, text: str) -> List[str]:
        """
        Splits Hindi text into individual checkable sentences.
        Handles danda (।), double danda (॥), question mark (?), exclamation (!),
        full stop (.), and newlines, while protecting abbreviations and decimals.
        """
        if not text or not text.strip():
            return []

        clean = self.normalize(text)

        # Protect known Hindi abbreviations
        placeholder = "@@DOT@@"
        protected = clean
        for abbr in self.HINDI_ABBREVIATIONS:
            def repl(match):
                return match.group(0).replace(".", placeholder)
            protected = re.sub(abbr, repl, protected)

        # Protect numeric decimals (e.g. 10.5 or १०.५)
        protected = re.sub(r"([\d०-९])\.([\d०-९])", rf"\1{placeholder}\2", protected)

        # Split on danda (।), double danda (॥), ?, !, newlines, or English period
        # followed by space or end-of-string
        raw_sentences = re.split(r"(?<=[।॥?!]|\.(?=\s|[A-Z\u0900-\u097F]|$))\s+", protected)

        sentences = []
        for s in raw_sentences:
            restored = s.replace(placeholder, ".").strip()
            # Clean leading/trailing stray delimiters
            if restored and len(restored) > 1:
                sentences.append(restored)

        return sentences

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenizes Hindi / Hinglish text preserving Devanagari words with matras and halant.
        Devanagari word pattern: matches sequences of Devanagari characters [\\u0900-\\u097F]
        alongside Latin words and numbers.
        """
        if not text:
            return []
        norm = self.normalize(text)
        # Matches Hindi words (including matras and virama), English words, and punctuation
        pattern = r"[\u0900-\u097F]+|[a-zA-Z0-9]+(?:[-'][a-zA-Z0-9]+)*|[^\w\s]"
        return re.findall(pattern, norm)


def get_normalizer(language_code: str) -> BaseNormalizer:
    """Factory retrieving the appropriate normalizer for a given language code."""
    lang = (language_code or "en").lower().strip()
    if lang == "hi":
        return HindiNormalizer()
    return EnglishNormalizer()

