"""
TruthLens - Evidence Collector & Ranker
Retrieves candidate articles, chunks them into coherent passages, validates verbatim
quotations against extracted text, enforces strict entity and semantic relevance thresholds,
and filters syndicated wire-service copies.
"""
import logging
import re
from typing import List, Optional, Set, Tuple
from urllib.parse import urlparse
from rank_bm25 import BM25Plus

from app.nlp.normalizers import get_normalizer
from app.schemas.claim import ExtractedClaim
from app.schemas.evidence import EvidenceCollectionResponse, EvidencePassage
from app.schemas.search import SearchResultItem
from app.services.evidence_deduplicator import evidence_deduplicator
from app.services.extractor import extract_article_from_url, ExtractionError
from app.services.passage_chunker import passage_chunker

logger = logging.getLogger("truthlens.evidence_collector")

STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "up", "about", "into", "over", "after", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "that", "this", "these", "those", "it", "its", "as", "their", "they"
}

STOPWORDS_HI = {
    "है", "हैं", "के", "में", "की", "को", "और", "से", "का", "था", "नहीं", "ने",
    "पर", "किया", "गया", "यह", "कि", "तो", "भी", "ही", "एक", "या", "हो", "हुए"
}

ACRONYM_MAP = {
    "rbi": ["आरबीआई", "रिजर्व बैंक"],
    "भारतीय रिजर्व बैंक": ["आरबीआई", "rbi"],
    "isro": ["इसरो", "भारतीय अंतरिक्ष"],
    "इसरो": ["isro", "भारतीय अंतरिक्ष अनुसंधान"],
    "who": ["डब्ल्यूएचओ", "विश्व स्वास्थ्य संगठन"],
    "nasa": ["नासा"],
    "नासा": ["nasa"],
    "bjp": ["बीजेपी", "भाजपा"],
    "inc": ["कांग्रेस"],
    "un": ["संयुक्त राष्ट्र", "यूएन"],
}

PRIMARY_DOMAINS_SUFFIXES = (
    ".gov", ".mil", ".gov.in", ".nic.in", ".gov.uk", ".europa.eu", ".edu", ".ac.in"
)

SECONDARY_NEWS_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "thehindu.com", "ndtv.com",
    "indianexpress.com", "hindustantimes.com", "nytimes.com", "wsj.com",
    "bloomberg.com", "aljazeera.com", "afp.com", "pti.in", "ani.in"
}


def classify_source_type(domain: str) -> str:
    """Classifies domain into primary, secondary (news), or other."""
    d = domain.lower().replace("www.", "")
    if any(d.endswith(sfx) for sfx in PRIMARY_DOMAINS_SUFFIXES):
        return "primary"
    if d in SECONDARY_NEWS_DOMAINS or any(d.endswith(f".{snd}") for snd in SECONDARY_NEWS_DOMAINS):
        return "secondary"
    return "other"


class EvidenceCollector:
    """
    Collects, chunks, verifies quotations, scores relevance, and deduplicates evidence.
    Enforces that unrelated passages (e.g. US student visa fraud for a Bollywood debut claim)
    are strictly rejected.
    """

    def __init__(self, top_k_passages: int = 5, min_relevance_threshold: float = 1.8):
        self.top_k_passages = top_k_passages
        self.min_relevance_threshold = min_relevance_threshold

    def is_passage_relevant_to_claim(
        self,
        claim: ExtractedClaim,
        passage_text: str,
        bm25_score: float,
        lang: str = "en"
    ) -> Tuple[bool, float, str]:
        """
        Validates whether an extracted passage is genuinely relevant to the claim.
        Rejects keyword-only false positives and completely unrelated topics.
        """
        normalizer = get_normalizer(lang)
        stops = STOPWORDS_HI if lang == "hi" else STOPWORDS_EN

        p_lower = passage_text.lower()
        c_lower = claim.claim_text.lower()

        # 1. Entity and Key Subject Anchoring
        # If the claim specifies named entities (people, orgs, movies, places):
        # Candidate passage must mention at least one core entity, acronym/alias, or distinctive proper noun.
        if claim.entities:
            matched_entity = False
            for ent in claim.entities:
                ent_clean = ent.strip().lower()
                if not ent_clean:
                    continue
                # 1a. Full entity phrase in passage
                if ent_clean in p_lower:
                    matched_entity = True
                    break
                # 1b. Acronym / cross-lingual transliteration mapping
                if ent_clean in ACRONYM_MAP:
                    if any(alt in p_lower for alt in ACRONYM_MAP[ent_clean]):
                        matched_entity = True
                        break
                # 1c. For multi-word entities, require either:
                # - at least 2 content tokens (e.g. 'student' AND 'year' for 'Student of the Year')
                # - OR a distinctive proper noun (>3 chars, not a generic word)
                ent_tokens = [t for t in normalizer.tokenize(ent_clean) if t not in stops and len(t) > 2]
                if len(ent_tokens) >= 2:
                    matched_tokens = sum(1 for t in ent_tokens if t in p_lower)
                    if matched_tokens >= 2 or matched_tokens == len(ent_tokens):
                        matched_entity = True
                        break
                elif len(ent_tokens) == 1:
                    t = ent_tokens[0]
                    # Single token must match and be distinctive (>4 chars)
                    if t in p_lower and len(t) > 4:
                        matched_entity = True
                        break

            if not matched_entity:
                return False, 0.0, "Passage does not mention any core named entities of the claim."

        # 2. Content Token Overlap Ratio
        claim_tokens = normalizer.tokenize(c_lower)
        claim_content = [t for t in claim_tokens if t not in stops and len(t) > 2]

        passage_tokens = normalizer.tokenize(p_lower)
        passage_content = set(t for t in passage_tokens if t not in stops and len(t) > 2)

        if not claim_content:
            return False, 0.0, "Claim contains insufficient checkable content terms."

        overlap_count = sum(1 for t in claim_content if t in passage_content)
        overlap_ratio = overlap_count / len(claim_content)

        # Minimum content overlap requirement (at least 20% of content tokens)
        if overlap_ratio < 0.20:
            return False, round(overlap_ratio, 3), f"Insufficient content overlap ({round(overlap_ratio*100)}%)."

        # 3. Minimum BM25 Score Threshold
        # Discard spurious background noise with low lexical weight
        if bm25_score < self.min_relevance_threshold and overlap_ratio < 0.35:
            return False, round(overlap_ratio, 3), f"Relevance score below calibrated threshold ({bm25_score:.2f})."

        # Calibrated normalized relevance score [0.0 - 1.0]
        relevance_score = min(1.0, max(0.25, round(overlap_ratio * 0.6 + min(bm25_score / 10.0, 0.4), 3)))
        return True, relevance_score, "Passage directly addresses claim assertions."

    def collect_evidence_for_claim(
        self,
        claim: ExtractedClaim,
        search_results: List[SearchResultItem]
    ) -> EvidenceCollectionResponse:
        """
        Fetches candidate publisher pages, extracts body text, chunks into passages,
        verifies verbatim quotations against extracted publisher text, filters out
        irrelevant topics, and applies syndication deduplication.
        """
        if not search_results:
            return EvidenceCollectionResponse(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                language=claim.language,
                passages=[],
                total_passages_found=0,
                independent_sources_count=0,
                syndicated_copies_count=0
            )

        candidate_passages: List[EvidencePassage] = []
        normalizer = get_normalizer(claim.language)

        # 1. Fetch original publisher pages and extract text
        for item in search_results:
            clean_url = evidence_deduplicator.canonicalize_url(item.url)
            try:
                article_data = extract_article_from_url(clean_url)
                article_text = article_data.get("text", "")
                if not article_text or len(article_text.strip()) < 50:
                    continue

                raw_chunks = passage_chunker.chunk_article(article_text, lang=claim.language)
                domain = article_data.get("domain", item.source_domain)
                publisher = domain.replace("www.", "").split(".")[0].capitalize()

                for pid, text_chunk, wcount in raw_chunks:
                    # Enforce Requirement: Verify that displayed quotation exists verbatim in extracted text
                    is_verbatim = text_chunk in article_text
                    if not is_verbatim:
                        continue

                    candidate_passages.append(
                        EvidencePassage(
                            passage_id=pid,
                            article_url=clean_url,
                            article_title=article_data.get("title", item.title),
                            canonical_domain=domain,
                            publisher_name=publisher,
                            passage_text=text_chunk,
                            word_count=wcount,
                            published_date=article_data.get("published_date") or item.published_date,
                            retrieved_at=item.retrieved_at,
                            relevance_score=0.0
                        )
                    )
            except ExtractionError as e:
                logger.info(f"Skipping unextractable URL {clean_url}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error extracting {clean_url}: {e}")
                continue

        if not candidate_passages:
            return EvidenceCollectionResponse(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                language=claim.language,
                passages=[],
                total_passages_found=0,
                independent_sources_count=0,
                syndicated_copies_count=0
            )

        # 2. BM25 Lexical Ranking
        tokenized_corpus = [normalizer.tokenize(p.passage_text) for p in candidate_passages]
        query_tokens = normalizer.tokenize(claim.claim_text)

        bm25 = BM25Plus(tokenized_corpus)
        bm25_scores = bm25.get_scores(query_tokens)

        # 3. Rigorous Relevance Filtering
        filtered_passages: List[EvidencePassage] = []
        for p, raw_bm25 in zip(candidate_passages, bm25_scores):
            is_rel, rel_score, reason = self.is_passage_relevant_to_claim(
                claim=claim,
                passage_text=p.passage_text,
                bm25_score=raw_bm25,
                lang=claim.language
            )
            if is_rel:
                p.relevance_score = rel_score
                filtered_passages.append(p)
            else:
                logger.debug(f"Discarding irrelevant passage from {p.canonical_domain}: {reason}")

        # If no passages passed the relevance threshold, return empty list!
        # DO NOT take unrelated top passages!
        if not filtered_passages:
            return EvidenceCollectionResponse(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                language=claim.language,
                passages=[],
                total_passages_found=0,
                independent_sources_count=0,
                syndicated_copies_count=0
            )

        # Sort candidate passages by calibrated relevance score descending
        filtered_passages.sort(key=lambda x: x.relevance_score, reverse=True)

        # 4. Detect and mark syndication
        updated_passages, indep_count, synd_count = evidence_deduplicator.detect_syndication(
            filtered_passages
        )

        # Keep top K highest scoring relevant passages
        top_passages = updated_passages[:self.top_k_passages]

        return EvidenceCollectionResponse(
            claim_id=claim.id,
            claim_text=claim.claim_text,
            language=claim.language,
            passages=top_passages,
            total_passages_found=len(filtered_passages),
            independent_sources_count=indep_count,
            syndicated_copies_count=synd_count
        )


# Global singleton
evidence_collector = EvidenceCollector()
