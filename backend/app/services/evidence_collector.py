"""
TruthLens 2.0 - Evidence Collector & Ranker
Retrieves candidate articles, chunks them into coherent passages, ranks them
against the claim using BM25, and filters syndicated wire-service copies.
"""
import logging
from typing import List, Optional
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


class EvidenceCollector:
    """
    Collects, chunks, ranks, and deduplicates evidence passages for factual claims.
    """

    def __init__(self, top_k_passages: int = 5):
        self.top_k_passages = top_k_passages

    def collect_evidence_for_claim(
        self,
        claim: ExtractedClaim,
        search_results: List[SearchResultItem]
    ) -> EvidenceCollectionResponse:
        """
        Fetches search lead articles, chunks into passages, scores with BM25,
        and applies syndication deduplication.
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

        # 1. Fetch and chunk candidate articles
        for item in search_results:
            clean_url = evidence_deduplicator.canonicalize_url(item.url)
            try:
                article_data = extract_article_from_url(clean_url)
                article_text = article_data.get("text", "")
                if not article_text:
                    continue

                raw_chunks = passage_chunker.chunk_article(article_text, lang=claim.language)
                domain = article_data.get("domain", item.source_domain)
                publisher = domain.replace("www.", "").split(".")[0].capitalize()

                for pid, text_chunk, wcount in raw_chunks:
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
        scores = bm25.get_scores(query_tokens)

        for p, score in zip(candidate_passages, scores):
            p.relevance_score = float(round(score, 4))

        # Sort candidate passages by BM25 relevance score descending
        candidate_passages.sort(key=lambda x: x.relevance_score, reverse=True)

        # 3. Detect and mark syndication
        updated_passages, indep_count, synd_count = evidence_deduplicator.detect_syndication(
            candidate_passages
        )

        # Keep top K highest scoring passages
        top_passages = updated_passages[:self.top_k_passages]

        return EvidenceCollectionResponse(
            claim_id=claim.id,
            claim_text=claim.claim_text,
            language=claim.language,
            passages=top_passages,
            total_passages_found=len(candidate_passages),
            independent_sources_count=indep_count,
            syndicated_copies_count=synd_count
        )


# Global singleton
evidence_collector = EvidenceCollector()
