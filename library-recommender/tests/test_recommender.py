"""Unit tests for the recommendation engine (pure numerical core + façade)."""
import pandas as pd

from app.extensions import db
from app.models import Book, Rating
from app.recommender import (
    build_matrix, user_similarity, predict_scores,
    popularity_ranking, RecommendationEngine,
)


# --- pure-function tests (no DB) -------------------------------------------
def _frame():
    return pd.DataFrame([
        # alice & bob agree, carol disagrees
        (1, 10, 5), (1, 11, 5), (1, 12, 1),
        (2, 10, 5), (2, 11, 4), (2, 12, 2),
        (3, 10, 1), (3, 11, 1), (3, 12, 5),
    ], columns=["user_id", "book_id", "score"])


def test_build_matrix_shape():
    m = build_matrix(_frame())
    assert m.shape == (3, 3)
    assert m.loc[1, 10] == 5


def test_similar_users_rank_higher():
    m = build_matrix(_frame())
    sims = user_similarity(m, target_user=1, method="cosine", min_overlap=2)
    # User 2 (agrees) should be more similar than user 3 (disagrees)
    assert sims.loc[2] > sims.loc[3]


def test_pearson_method_runs():
    m = build_matrix(_frame())
    sims = user_similarity(m, target_user=1, method="pearson", min_overlap=2)
    assert 2 in sims.index


def test_min_overlap_filters_out_thin_pairs():
    frame = pd.DataFrame([
        (1, 10, 5), (1, 11, 4),
        (2, 10, 5),               # only ONE co-rated book with user 1
    ], columns=["user_id", "book_id", "score"])
    m = build_matrix(frame)
    sims = user_similarity(m, target_user=1, min_overlap=2)
    assert 2 not in sims.index  # dropped for insufficient overlap


def test_predict_scores_returns_unrated_only():
    frame = pd.DataFrame([
        (1, 10, 5), (1, 12, 1),         # user 1 has NOT rated book 11
        (2, 10, 5), (2, 11, 5), (2, 12, 1),
    ], columns=["user_id", "book_id", "score"])
    m = build_matrix(frame)
    sims = user_similarity(m, 1, min_overlap=2)
    preds = predict_scores(m, 1, sims)
    assert 11 in preds.index   # the unrated book gets a prediction
    assert 10 not in preds.index  # already-rated books are excluded


def test_popularity_bayesian_prefers_well_supported_books():
    frame = pd.DataFrame([
        (1, 10, 5),                                          # ONE 5-star vote
        (2, 11, 5), (3, 11, 5), (4, 11, 5), (5, 11, 5), (6, 11, 4),  # 5 strong votes
        (7, 12, 1), (8, 12, 1),                              # drags global mean down
    ], columns=["user_id", "book_id", "score"])
    ranking = popularity_ranking(frame, min_votes=3)
    # The well-supported book 11 (avg 4.8 over 5 votes) should out-rank the
    # single-vote book 10, whose lone 5 is shrunk toward the global mean.
    assert ranking.index[0] == 11
    assert ranking.loc[11] > ranking.loc[10]


# --- façade tests (with DB) ------------------------------------------------
def test_engine_recommends_expected_book(app, seeded):
    with app.app_context():
        engine = RecommendationEngine(db, Rating, Book, app.config)
        recs = engine.recommend_for(seeded["target"])
        rec_ids = [r.book_id for r in recs]
        # target likes Fantasy A; similar users (alice/bob) love Fantasy B,
        # which target hasn't read -> it should be recommended.
        assert seeded["books"]["Fantasy B"] in rec_ids
        assert all(r.method == "collaborative" for r in recs)


def test_engine_explanations_present(app, seeded):
    with app.app_context():
        engine = RecommendationEngine(db, Rating, Book, app.config)
        recs = engine.recommend_for(seeded["target"])
        assert recs and all(r.reason for r in recs)


def test_cold_start_falls_back_to_popularity(app, seeded):
    with app.app_context():
        # A brand-new user with no ratings -> popularity recommendations
        from app.models import User
        u = User(name="newbie", email="newbie@t.dev")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()
        engine = RecommendationEngine(db, Rating, Book, app.config)
        recs = engine.recommend_for(u.id)
        assert recs and all(r.method == "popularity" for r in recs)
