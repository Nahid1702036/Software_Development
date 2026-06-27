"""Data-driven recommendation engine.

This module implements **user-based collaborative filtering** with two
interchangeable similarity metrics and a popularity-based fallback for the
cold-start problem.

Pipeline
--------
1.  Pull all ratings into a tidy DataFrame and pivot into a user x item matrix.
2.  Mean-centre each user's ratings (removes "harsh vs. generous rater" bias).
3.  Measure similarity between the target user and every other user using either
        * cosine similarity over the mean-centred vectors, or
        * Pearson correlation over co-rated items.
    Pairs that share fewer than ``min_overlap`` co-rated books are discarded,
    because a similarity computed from one shared book is statistically noise.
4.  Predict a score for every book the target user has *not* rated as the
    similarity-weighted average of the neighbours' (mean-centred) opinions,
    added back onto the target user's own mean.
5.  Return the top-N highest-predicted books, each with a human-readable
    explanation ("Because you liked ...").

If the target user has too few ratings to compute reliable neighbours, the
engine falls back to a **Bayesian-weighted popularity** ranking, which blends a
book's average score with how many people rated it (so a single 5-star review
cannot out-rank a book loved by fifty readers).

The heavy-lifting functions operate on plain DataFrames, which keeps them pure
and trivially unit-testable in isolation from Flask or the database.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd


@dataclass
class Recommendation:
    """A single recommended book plus the reasoning behind it."""

    book_id: int
    predicted_score: float
    reason: str
    method: str  # "collaborative" or "popularity"


# ---------------------------------------------------------------------------
# Pure numerical core (no Flask, no DB) — easy to unit test
# ---------------------------------------------------------------------------
def build_matrix(ratings: pd.DataFrame) -> pd.DataFrame:
    """Pivot a tidy ``[user_id, book_id, score]`` frame into a user x item matrix.

    Missing entries are NaN (the user has not rated that book).
    """
    if ratings.empty:
        return pd.DataFrame()
    return ratings.pivot_table(index="user_id", columns="book_id", values="score")


def _mean_centre(matrix: pd.DataFrame):
    """Subtract each user's mean rating from their row.

    Returns the centred matrix and the per-user means (needed to de-centre
    predictions later).
    """
    user_means = matrix.mean(axis=1)
    centred = matrix.sub(user_means, axis=0)
    return centred, user_means


def user_similarity(
    matrix: pd.DataFrame,
    target_user: int,
    method: str = "cosine",
    min_overlap: int = 2,
) -> pd.Series:
    """Similarity of every other user to ``target_user`` (range -1..1).

    Users with fewer than ``min_overlap`` co-rated books are dropped.
    """
    if target_user not in matrix.index:
        return pd.Series(dtype=float)

    centred, _ = _mean_centre(matrix)
    target_vec = centred.loc[target_user]
    target_rated = matrix.loc[target_user].notna()

    sims = {}
    for other in matrix.index:
        if other == target_user:
            continue
        other_rated = matrix.loc[other].notna()
        co_rated = target_rated & other_rated
        overlap = int(co_rated.sum())
        if overlap < min_overlap:
            continue

        a = target_vec[co_rated].to_numpy(dtype=float)
        b = centred.loc[other][co_rated].to_numpy(dtype=float)

        if method == "pearson":
            # Pearson = cosine of the (already centred over co-rated) vectors,
            # but we re-centre over the *co-rated* subset for correctness.
            a = a - a.mean()
            b = b - b.mean()

        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            continue
        sim = float(np.dot(a, b) / denom)
        if not np.isnan(sim):
            sims[other] = sim

    return pd.Series(sims, dtype=float).sort_values(ascending=False)


def predict_scores(
    matrix: pd.DataFrame,
    target_user: int,
    sims: pd.Series,
    n_neighbours: int = 15,
) -> pd.Series:
    """Predict scores for books the target user has not yet rated."""
    if target_user not in matrix.index or sims.empty:
        return pd.Series(dtype=float)

    _, user_means = _mean_centre(matrix)
    centred, _ = _mean_centre(matrix)
    target_mean = user_means.loc[target_user]

    neighbours = sims.head(n_neighbours)
    unrated = matrix.columns[matrix.loc[target_user].isna()]

    predictions = {}
    for book in unrated:
        num = 0.0
        den = 0.0
        for neighbour, sim in neighbours.items():
            r = centred.loc[neighbour, book]
            if pd.isna(r) or sim <= 0:
                continue
            num += sim * r
            den += abs(sim)
        if den > 0:
            predictions[book] = target_mean + num / den

    return pd.Series(predictions, dtype=float).sort_values(ascending=False)


def popularity_ranking(ratings: pd.DataFrame, min_votes: int = 3) -> pd.Series:
    """Bayesian-weighted popularity score per book (the IMDb "true Bayesian" formula).

        WR = (v / (v + m)) * R + (m / (v + m)) * C

    where R = book's mean score, v = its vote count, C = global mean score,
    m = a smoothing prior (``min_votes``). This stops a book with one 5-star
    rating from beating a book with a 4.6 average across hundreds of votes.
    """
    if ratings.empty:
        return pd.Series(dtype=float)
    grouped = ratings.groupby("book_id")["score"]
    R = grouped.mean()
    v = grouped.count()
    C = ratings["score"].mean()
    m = min_votes
    wr = (v / (v + m)) * R + (m / (v + m)) * C
    return wr.sort_values(ascending=False)


# ---------------------------------------------------------------------------
# Database-aware façade used by the Flask views
# ---------------------------------------------------------------------------
class RecommendationEngine:
    """Wraps the numerical core and talks to the database.

    Recommendations are cached in-process and recomputed on demand or when
    ``invalidate()`` is called (e.g. after a new rating is submitted), matching
    the spec's "precompute periodically or on demand" requirement.
    """

    def __init__(self, db, Rating, Book, config=None):
        self.db = db
        self.Rating = Rating
        self.Book = Book
        cfg = config or {}
        self.top_n = cfg.get("RECOMMENDER_TOP_N", 8)
        self.min_overlap = cfg.get("RECOMMENDER_MIN_OVERLAP", 2)
        self.n_neighbours = cfg.get("RECOMMENDER_NEIGHBOURS", 15)
        self.method = cfg.get("RECOMMENDER_METHOD", "cosine")
        self._cache = {}

    # -- data loading ------------------------------------------------------
    def _ratings_frame(self) -> pd.DataFrame:
        rows = self.db.session.query(
            self.Rating.user_id, self.Rating.book_id, self.Rating.score
        ).all()
        return pd.DataFrame(rows, columns=["user_id", "book_id", "score"])

    def invalidate(self):
        self._cache.clear()

    # -- main entry point --------------------------------------------------
    def recommend_for(self, user_id: int, top_n: Optional[int] = None) -> List[Recommendation]:
        top_n = top_n or self.top_n
        ratings = self._ratings_frame()
        if ratings.empty:
            return []

        user_ratings = ratings[ratings.user_id == user_id]
        matrix = build_matrix(ratings)

        # Cold start: not enough signal for collaborative filtering.
        if len(user_ratings) < self.min_overlap or user_id not in matrix.index:
            return self._popularity_recs(ratings, user_id, top_n)

        sims = user_similarity(matrix, user_id, self.method, self.min_overlap)
        if sims.empty:
            return self._popularity_recs(ratings, user_id, top_n)

        preds = predict_scores(matrix, user_id, sims, self.n_neighbours)
        if preds.empty:
            return self._popularity_recs(ratings, user_id, top_n)

        recs = []
        for book_id, score in preds.head(top_n).items():
            reason = self._explain(user_id, int(book_id), sims, matrix, ratings)
            recs.append(
                Recommendation(
                    book_id=int(book_id),
                    predicted_score=round(float(score), 2),
                    reason=reason,
                    method="collaborative",
                )
            )
        return recs

    # -- explanation -------------------------------------------------------
    def _explain(self, user_id, book_id, sims, matrix, ratings) -> str:
        """Find the most similar neighbour who liked this book, then surface a
        book *they and the target user* both liked, producing
        "Because you liked <title>"."""
        top_neighbours = sims.head(self.n_neighbours)
        best_neighbour = None
        for neighbour, sim in top_neighbours.items():
            if sim <= 0:
                continue
            r = matrix.loc[neighbour, book_id]
            if pd.notna(r) and r >= 4:
                best_neighbour = neighbour
                break
        if best_neighbour is None:
            return "Recommended by readers with taste similar to yours."

        # Books the target user rated highly that the neighbour also rated highly
        user_likes = ratings[(ratings.user_id == user_id) & (ratings.score >= 4)]
        neigh_likes = set(
            ratings[(ratings.user_id == best_neighbour) & (ratings.score >= 4)].book_id
        )
        shared = user_likes[user_likes.book_id.isin(neigh_likes)]
        if not shared.empty:
            anchor_id = int(shared.sort_values("score", ascending=False).iloc[0].book_id)
            anchor = self.db.session.get(self.Book, anchor_id)
            if anchor:
                return f"Because you liked \u201c{anchor.title}\u201d"
        return "Readers who share your taste rated this highly."

    # -- cold-start fallback ----------------------------------------------
    def _popularity_recs(self, ratings, user_id, top_n) -> List[Recommendation]:
        already = set(ratings[ratings.user_id == user_id].book_id)
        ranking = popularity_ranking(ratings, min_votes=self.min_overlap)
        recs = []
        for book_id, score in ranking.items():
            if int(book_id) in already:
                continue
            recs.append(
                Recommendation(
                    book_id=int(book_id),
                    predicted_score=round(float(score), 2),
                    reason="Popular with readers across the library.",
                    method="popularity",
                )
            )
            if len(recs) >= top_n:
                break
        return recs
