"""
TruthLens 2.0 - Semantic Passage Chunker
Chunks long news articles into coherent, overlapping passages of 100-180 words.
Preserves complete sentence boundaries and exact verbatim quotations for transparency.
"""
import hashlib
from typing import List, Tuple
from app.nlp.normalizers import get_normalizer


class PassageChunker:
    """
    Splits long article text into context-rich passages for retrieval and NLI.
    """

    def __init__(self, target_words: int = 140, overlap_sentences: int = 1):
        self.target_words = target_words
        self.overlap_sentences = overlap_sentences

    def chunk_article(
        self,
        article_text: str,
        lang: str = "en"
    ) -> List[Tuple[str, str, int]]:
        """
        Chunks article into passages.
        
        Returns:
            List[Tuple[passage_id, passage_text, word_count]]
        """
        if not article_text or not article_text.strip():
            return []

        normalizer = get_normalizer(lang)
        sentences = normalizer.split_sentences(article_text)

        if not sentences:
            return []

        passages: List[Tuple[str, str, int]] = []
        current_chunk_sentences: List[str] = []
        current_word_count = 0

        for sentence in sentences:
            s_clean = sentence.strip()
            if not s_clean:
                continue

            words = s_clean.split()
            word_count = len(words)

            current_chunk_sentences.append(s_clean)
            current_word_count += word_count

            # If chunk reached target size, finalize passage
            if current_word_count >= self.target_words:
                passage_text = " ".join(current_chunk_sentences)
                passage_id = self._generate_passage_id(passage_text)
                passages.append((passage_id, passage_text, current_word_count))

                # Slide window by keeping trailing overlap sentences
                if self.overlap_sentences > 0 and len(current_chunk_sentences) > self.overlap_sentences:
                    current_chunk_sentences = current_chunk_sentences[-self.overlap_sentences:]
                    current_word_count = sum(len(s.split()) for s in current_chunk_sentences)
                else:
                    current_chunk_sentences = []
                    current_word_count = 0

        # Trailing remainder
        if current_chunk_sentences:
            passage_text = " ".join(current_chunk_sentences)
            # Only keep if substantial (at least 20 words or solitary remainder)
            if current_word_count >= 20 or not passages:
                passage_id = self._generate_passage_id(passage_text)
                passages.append((passage_id, passage_text, current_word_count))

        return passages

    def _generate_passage_id(self, passage_text: str) -> str:
        """Deterministic passage hash ID."""
        digest = hashlib.sha256(passage_text.encode("utf-8")).hexdigest()[:12]
        return f"psg_{digest}"


# Global singleton
passage_chunker = PassageChunker()

