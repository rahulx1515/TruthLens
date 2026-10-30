"""
TruthLens 2.0 - Syndication & Duplication Detector
Canonicalizes URLs and detects wire-service syndication (e.g. PTI, ANI, Reuters, AP)
using shingle-based Jaccard similarity. Prevents cloned articles from artificially inflating
source independence.
"""
from typing import Dict, List, Set, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import hashlib

from app.schemas.evidence import EvidencePassage


class EvidenceDeduplicator:
    """
    Detects duplicate and syndicated evidence passages across different publishers.
    """

    TRACKING_PARAMS = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "msclkid", "ref", "source", "ref_src", "_ga", "session_id"
    }

    def __init__(self, jaccard_threshold: float = 0.65):
        self.jaccard_threshold = jaccard_threshold

    def canonicalize_url(self, raw_url: str) -> str:
        """
        Strips tracking query parameters, hashes, and normalizes URL.
        """
        if not raw_url:
            return ""

        parsed = urlparse(raw_url.strip())
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Filter out tracking query parameters
        qs = parse_qs(parsed.query, keep_blank_values=False)
        clean_qs = {k: v for k, v in qs.items() if k.lower() not in self.TRACKING_PARAMS}
        sorted_query = urlencode(sorted(clean_qs.items()), doseq=True)

        path = parsed.path.rstrip("/")
        if not path:
            path = ""

        canonical = urlunparse((
            parsed.scheme.lower() or "https",
            netloc,
            path,
            "",  # params
            sorted_query,
            ""   # fragment
        ))
        return canonical

    def detect_syndication(
        self,
        passages: List[EvidencePassage]
    ) -> Tuple[List[EvidencePassage], int, int]:
        """
        Analyzes passages for near-identical wire copy republication.
        Groups syndicated copies into clusters, marking duplicates.
        
        Returns:
            Tuple[updated_passages, independent_count, syndicated_count]
        """
        if not passages:
            return [], 0, 0

        # Compute word 3-gram sets for each passage
        shingles_list: List[Set[Tuple[str, ...]]] = []
        for p in passages:
            words = [w.lower() for w in p.passage_text.split() if len(w) > 1]
            if len(words) >= 3:
                shingles = {tuple(words[i:i+3]) for i in range(len(words) - 2)}
            else:
                shingles = {tuple(words)}
            shingles_list.append(shingles)

        n = len(passages)
        # Cluster assignments
        clusters: Dict[int, str] = {}
        cluster_primaries: Dict[str, str] = {}  # cluster_id -> primary_source_url

        for i in range(n):
            if i in clusters:
                continue

            # Start new cluster with passage i as primary
            cluster_id = f"cls_{hashlib.md5(passages[i].article_url.encode()).hexdigest()[:8]}"
            clusters[i] = cluster_id
            cluster_primaries[cluster_id] = passages[i].article_url
            passages[i].cluster_id = cluster_id
            passages[i].is_syndicated_copy = False

            # Check all subsequent passages for syndication similarity
            for j in range(i + 1, n):
                if j in clusters:
                    continue

                sim = self._jaccard_similarity(shingles_list[i], shingles_list[j])
                if sim >= self.jaccard_threshold:
                    clusters[j] = cluster_id
                    passages[j].cluster_id = cluster_id
                    passages[j].is_syndicated_copy = True
                    passages[j].primary_source_url = cluster_primaries[cluster_id]

        independent_clusters = set(clusters.values())
        syndicated_count = sum(1 for p in passages if p.is_syndicated_copy)
        independent_count = len(independent_clusters)

        return passages, independent_count, syndicated_count

    def _jaccard_similarity(self, set_a: Set[Tuple[str, ...]], set_b: Set[Tuple[str, ...]]) -> float:
        """Computes Jaccard index between two shingle sets."""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        if union == 0:
            return 0.0
        return intersection / union


# Global singleton
evidence_deduplicator = EvidenceDeduplicator()

