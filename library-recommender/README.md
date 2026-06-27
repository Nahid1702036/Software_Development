# Lumière Library — Data-Driven Book Recommendation Engine

A web application that recommends books to readers based on their ratings,
using **user-based collaborative filtering** (cosine *and* Pearson similarity)
with a Bayesian popularity fallback for new users. Built with **Flask** and
**Pandas / NumPy**.

> Software Engineering course assignment — **Project 7: Library Book
> Recommendation Engine (Data-Driven)**.

---

## Features

| Area | What it does |
|------|--------------|
| **Accounts** | Register, log in/out, editable profile (Flask-Login, hashed passwords) |
| **Catalog** | Browse, full-text search by title/author, filter by genre, sort by rating/popularity/year |
| **Ratings & Reviews** | Rate any book 1–5 stars with an optional text review; re-rating updates in place |
| **Recommendations** | Personalised "Recommended for You" feed with a **reason** for each pick ("Because you liked …") |
| **Cold start** | New users see Bayesian-weighted popular books until they've rated enough to personalise |
| **Discovery** | "Readers also enjoyed" on every book page |
| **Admin panel** | Add / edit / delete books, ratings-distribution chart, most-rated & highest-rated tables |

## The recommendation algorithm

Implemented in [`app/recommender.py`](app/recommender.py).

1. **Build matrix** — pivot all ratings into a *user × book* matrix.
2. **Mean-centre** each user's row, removing the "harsh vs. generous rater" bias.
3. **Similarity** — for the target user, measure similarity to every other user
   using **cosine** or **Pearson** over their co-rated books. Pairs sharing
   fewer than `RECOMMENDER_MIN_OVERLAP` books are discarded as statistical noise.
4. **Predict** unrated books as the similarity-weighted average of the nearest
   neighbours' opinions, added back onto the user's own mean.
5. **Explain** — surface a book the user and a top neighbour both rated highly.
6. **Cold start** — if there isn't enough signal, fall back to a
   **Bayesian-weighted popularity** ranking (the IMDb "true Bayesian" formula),
   so a single 5-star review can't out-rank a book loved by fifty readers.

The pure numerical functions take plain DataFrames, which makes them
trivial to unit-test in isolation from Flask and the database.

## Tech stack

- **Backend:** Python 3, Flask (application-factory pattern, 3 blueprints)
- **ORM / DB:** SQLAlchemy + SQLite by default (swap to MySQL/PostgreSQL via `DATABASE_URL`)
- **Auth:** Flask-Login with Werkzeug password hashing
- **Data / ML:** Pandas, NumPy
- **Frontend:** server-rendered Jinja2 templates, hand-written CSS (no framework)
- **Testing:** PyTest (unit + integration)

## Project structure

```
library-recommender/
├── run.py                    # entry point
├── config.py                 # dev / testing / production configs
├── requirements.txt
├── generate_seed.py          # regenerates the sample CSV dataset
├── seed_data/
│   ├── books.csv             # 20 books
│   ├── users.csv             # 30 readers
│   └── ratings.csv           # 334 ratings (clustered taste tribes)
├── app/
│   ├── __init__.py           # app factory + CLI commands
│   ├── extensions.py         # db, login_manager
│   ├── models.py             # User, Book, Rating
│   ├── recommender.py        # collaborative-filtering engine
│   ├── seed.py               # CSV → database loader
│   ├── auth/                 # register / login / logout
│   ├── main/                 # dashboard, catalog, detail, rating, profile
│   ├── admin/                # management + analytics
│   ├── templates/            # Jinja2 views
│   └── static/css/style.css  # "reading-room" theme
└── tests/                    # 23 PyTest tests
```

## Getting started

```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create tables and load the sample dataset
flask --app run seed --reset

# 4. Run
flask --app run run                # or:  python run.py
# visit http://127.0.0.1:5000
```

### Demo accounts (created by the seeder)

| Role | Email | Password |
|------|-------|----------|
| Reader | `nahid@readers.dev` | `password123` |
| Admin  | `admin@library.dev` | `admin123` |

(Every seeded reader uses the password `password123`.)

## Running the tests

```bash
pytest -q
```

All 23 tests should pass — covering the engine maths (similarity, prediction,
overlap filtering, Bayesian popularity), authentication, access control,
rating persistence/idempotency, and admin guards.

## Configuration

Tunable in `config.py` (or via environment variables):

| Setting | Default | Meaning |
|---------|---------|---------|
| `RECOMMENDER_METHOD` | `cosine` | `cosine` or `pearson` |
| `RECOMMENDER_TOP_N` | `8` | books shown on the dashboard |
| `RECOMMENDER_MIN_OVERLAP` | `2` | min co-rated books for two users to be neighbours |
| `RECOMMENDER_NEIGHBOURS` | `15` | how many similar users to weigh |
| `DATABASE_URL` | SQLite file | point at MySQL/PostgreSQL for production |

## Regenerating the dataset

```bash
python generate_seed.py            # rewrites seed_data/*.csv (seeded RNG, reproducible)
flask --app run seed --reset       # reload into the database
```

## License

Course assignment — for educational use.
