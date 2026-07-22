"""
Feature 10 — TF-IDF + Cosine Similarity clustering for community scam reports.

MVP-DEPTH: This uses threshold-based single-pass clustering (simple & fast).
A production system would use DBSCAN or hierarchical clustering on TF-IDF
vectors, re-run on a schedule, and store cluster centroids for incremental
updates without full re-computation.
"""
from __future__ import annotations

import logging
from collections import defaultdict, Counter
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Similarity threshold above which two reports are considered the same cluster
SIMILARITY_THRESHOLD = 0.35


def cluster_reports(
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Cluster a list of report dicts by text similarity.

    Each dict must have: id, report_text, scam_type (optional).
    Returns the same list with 'cluster_id' assigned to each report.
    """
    if not reports:
        return []

    texts = [r["report_text"] for r in reports]

    if len(texts) == 1:
        reports[0]["cluster_id"] = 0
        return reports

    # ── TF-IDF vectorisation ───────────────────────────────────────────────────
    try:
        vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            stop_words="english",      # will be supplemented with Hindi stopwords later
            min_df=1,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf_matrix)
    except Exception as exc:
        logger.error("TF-IDF computation failed: %s", exc)
        # Fallback: put everything in cluster 0
        for r in reports:
            r["cluster_id"] = 0
        return reports

    # ── Single-pass threshold clustering ──────────────────────────────────────
    cluster_ids = [-1] * len(reports)
    next_cluster = 0

    for i in range(len(reports)):
        if cluster_ids[i] != -1:
            continue  # already assigned
        cluster_ids[i] = next_cluster
        # Find all un-assigned reports similar enough to i
        for j in range(i + 1, len(reports)):
            if cluster_ids[j] == -1 and sim_matrix[i, j] >= SIMILARITY_THRESHOLD:
                cluster_ids[j] = next_cluster
        next_cluster += 1

    for i, report in enumerate(reports):
        report["cluster_id"] = cluster_ids[i]

    logger.info("Clustered %d reports into %d clusters", len(reports), next_cluster)
    return reports


def build_cluster_summaries(
    clustered_reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produce summary dicts per cluster for the API response.
    """
    by_cluster: dict[int, list[dict]] = defaultdict(list)
    for r in clustered_reports:
        by_cluster[r.get("cluster_id", 0)].append(r)

    summaries = []
    for cid, group in sorted(by_cluster.items()):
        # Representative: first report in the cluster (longest text wins)
        rep = max(group, key=lambda r: len(r["report_text"]))
        scam_types = [r.get("scam_type") for r in group if r.get("scam_type")]
        common_type = Counter(scam_types).most_common(1)[0][0] if scam_types else None
        summaries.append({
            "cluster_id": cid,
            "report_count": len(group),
            "representative_text": rep["report_text"][:200],
            "common_scam_type": common_type,
        })

    return summaries


def find_similar_count(new_text: str, existing_texts: list[str]) -> int:
    """
    Count how many existing reports are similar to a new report.
    Used when accepting a new submission to surface "N similar reports found".
    """
    if not existing_texts:
        return 0
    try:
        all_texts = existing_texts + [new_text]
        vectorizer = TfidfVectorizer(max_features=300, ngram_range=(1, 2), min_df=1)
        matrix = vectorizer.fit_transform(all_texts)
        sims = cosine_similarity(matrix[-1:], matrix[:-1])[0]
        return int(np.sum(sims >= SIMILARITY_THRESHOLD))
    except Exception as exc:
        logger.warning("Similarity count failed: %s", exc)
        return 0
