"""Generate realistic, clustered seed data so collaborative filtering has signal.

Run once: `python generate_seed.py`. Produces seed_data/books.csv and
seed_data/ratings.csv. Users are assigned to "taste tribes" that prefer certain
genres, which makes similar-user neighbourhoods emerge naturally.
"""
import csv
import os
import random

random.seed(42)
HERE = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(HERE, "seed_data")
os.makedirs(SEED_DIR, exist_ok=True)

# (title, author, genre, year, isbn, cover_color, description)
BOOKS = [
    ("The Name of the Wind", "Patrick Rothfuss", "Fantasy", 2007, "9780756404741", "#6b2d2d", "A gifted young man recounts his rise from orphan to legendary arcanist."),
    ("A Game of Thrones", "George R. R. Martin", "Fantasy", 1996, "9780553103540", "#4a3b2a", "Noble houses vie for an iron throne amid winter's slow return."),
    ("The Way of Kings", "Brandon Sanderson", "Fantasy", 2010, "9780765326355", "#2d4a4a", "On a storm-scoured world, warriors and scholars chase an ancient secret."),
    ("Mistborn: The Final Empire", "Brandon Sanderson", "Fantasy", 2006, "9780765311788", "#3a2d4a", "A street thief joins a crew plotting to topple an immortal god-emperor."),
    ("Dune", "Frank Herbert", "Sci-Fi", 1965, "9780441172719", "#8a5a2b", "A desert planet, a precious spice, and a boy bred to be a messiah."),
    ("Project Hail Mary", "Andy Weir", "Sci-Fi", 2021, "9780593135204", "#1f3a5f", "A lone astronaut wakes with no memory and the fate of Earth on his shoulders."),
    ("Neuromancer", "William Gibson", "Sci-Fi", 1984, "9780441569595", "#2a2a3a", "A burned-out hacker takes one last job in a neon cyberspace future."),
    ("The Three-Body Problem", "Liu Cixin", "Sci-Fi", 2008, "9780765382030", "#3a2a2a", "A secret signal to the stars sets humanity on a collision course."),
    ("Gone Girl", "Gillian Flynn", "Mystery", 2012, "9780307588364", "#444444", "A wife vanishes on her anniversary and nothing is what it seems."),
    ("The Girl with the Dragon Tattoo", "Stieg Larsson", "Mystery", 2005, "9780307269751", "#1a1a1a", "A journalist and a hacker unravel a decades-old disappearance."),
    ("The Silent Patient", "Alex Michaelides", "Mystery", 2019, "9781250301697", "#2d3a4a", "A woman shoots her husband, then never speaks another word."),
    ("Big Little Lies", "Liane Moriarty", "Mystery", 2014, "9780399167065", "#5f3a4a", "Three mothers, a schoolyard secret, and a death no one saw coming."),
    ("Pride and Prejudice", "Jane Austen", "Classic", 1813, "9780141439518", "#3a4a2d", "Wit, pride, and slow-burning love among the English gentry."),
    ("Crime and Punishment", "Fyodor Dostoevsky", "Classic", 1866, "9780486415871", "#4a2d2d", "A destitute student commits murder and is consumed by his conscience."),
    ("1984", "George Orwell", "Classic", 1949, "9780451524935", "#2a2a2a", "Under the eye of Big Brother, one man dares to think freely."),
    ("To Kill a Mockingbird", "Harper Lee", "Classic", 1960, "9780061120084", "#5a4a2a", "A child watches her father defend an innocent man in the segregated South."),
    ("Sapiens", "Yuval Noah Harari", "Non-Fiction", 2011, "9780062316097", "#8a6a2a", "A sweeping account of how an unremarkable ape came to rule the planet."),
    ("Educated", "Tara Westover", "Non-Fiction", 2018, "9780399590504", "#3a3a2a", "A girl kept from school claws her way to a Cambridge doctorate."),
    ("Thinking, Fast and Slow", "Daniel Kahneman", "Non-Fiction", 2011, "9780374533557", "#2a3a3a", "A Nobel laureate maps the two systems that drive how we think."),
    ("The Body Keeps the Score", "Bessel van der Kolk", "Non-Fiction", 2014, "9780670785933", "#4a2a3a", "How trauma reshapes body and brain — and the paths to healing."),
]

GENRES = ["Fantasy", "Sci-Fi", "Mystery", "Classic", "Non-Fiction"]

# Each "tribe" loves two genres, is lukewarm on others.
TRIBES = [
    {"loves": {"Fantasy", "Sci-Fi"}},
    {"loves": {"Mystery", "Classic"}},
    {"loves": {"Non-Fiction", "Classic"}},
    {"loves": {"Sci-Fi", "Non-Fiction"}},
    {"loves": {"Fantasy", "Mystery"}},
]

FIRST = ["Alice", "Ben", "Chloe", "Daniel", "Ella", "Farid", "Grace", "Hiro", "Ivy", "Jamal",
         "Kira", "Leo", "Mona", "Nahid", "Omar", "Priya", "Quinn", "Rosa", "Sam", "Tara",
         "Umar", "Vera", "Wei", "Xan", "Yara", "Zane", "Anya", "Bilal", "Cleo", "Dina"]

users = []
for i, name in enumerate(FIRST):
    tribe = TRIBES[i % len(TRIBES)]
    users.append({
        "name": name,
        "email": f"{name.lower()}@readers.dev",
        "password": "password123",
        "tribe": tribe,
    })

# Write books.csv
with open(os.path.join(SEED_DIR, "books.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["title", "author", "genre", "year", "isbn", "cover_color", "description"])
    for b in BOOKS:
        w.writerow(b)

# Write ratings.csv — each user rates 8..15 books, biased by tribe
review_snippets = [
    "Couldn't put it down.", "A bit slow in the middle but worth it.",
    "Beautifully written.", "Not my usual genre, pleasantly surprised.",
    "Overhyped, honestly.", "Re-read it twice.", "The ending floored me.",
    "Solid, if predictable.", "Recommended it to everyone I know.",
]

with open(os.path.join(SEED_DIR, "ratings.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["user_email", "book_isbn", "score", "review"])
    for u in users:
        n = random.randint(8, 15)
        chosen = random.sample(BOOKS, n)
        for b in chosen:
            genre = b[2]
            if genre in u["tribe"]["loves"]:
                score = random.choices([3, 4, 5], weights=[1, 3, 5])[0]
            else:
                score = random.choices([1, 2, 3, 4], weights=[2, 3, 3, 2])[0]
            review = random.choice(review_snippets) if random.random() < 0.35 else ""
            w.writerow([u["email"], b[4], score, review])

# Also emit a users.csv so the seeder can create accounts with names/bios
with open(os.path.join(SEED_DIR, "users.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["name", "email", "password", "bio"])
    for u in users:
        loves = " & ".join(sorted(u["tribe"]["loves"]))
        w.writerow([u["name"], u["email"], u["password"], f"Into {loves}."])

print("Seed data written to", SEED_DIR)
for fn in ("books.csv", "ratings.csv", "users.csv"):
    path = os.path.join(SEED_DIR, fn)
    print(f"  {fn}: {sum(1 for _ in open(path)) - 1} rows")
