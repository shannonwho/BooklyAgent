"""Generate ~500 books with realistic data."""
import random
from datetime import datetime, timedelta
from faker import Faker
from .models import Book, Genre

fake = Faker()

# Real public domain authors and some fictional ones
AUTHORS = [
    "Jane Austen", "Charles Dickens", "Mark Twain", "Emily Bronte",
    "Oscar Wilde", "Leo Tolstoy", "Fyodor Dostoevsky", "Victor Hugo",
    "Jules Verne", "H.G. Wells", "Arthur Conan Doyle", "Edgar Allan Poe",
    "Herman Melville", "Nathaniel Hawthorne", "Louisa May Alcott",
    "Robert Louis Stevenson", "Bram Stoker", "Mary Shelley",
    # Modern fictional authors
    "Sarah Mitchell", "James Chen", "Elena Rodriguez", "Michael O'Brien",
    "Aisha Patel", "Thomas Anderson", "Jennifer Lee", "David Kim",
    "Rachel Green", "Marcus Johnson", "Sophia Williams", "Daniel Brown",
    "Emma Thompson", "Ryan Martinez", "Lisa Wang", "Christopher Davis",
    "Amanda Foster", "Brian Wilson", "Nicole Taylor", "Kevin Moore",
    "Jessica Clark", "Andrew Hill", "Stephanie Young", "Patrick Hall",
]

# Title templates by genre
TITLE_TEMPLATES = {
    Genre.FICTION: [
        "The {adj} {noun}", "A {noun} in {place}", "{name}'s {noun}",
        "The Last {noun}", "Beyond the {noun}", "When {noun} Falls",
        "The {adj} House", "Whispers of {noun}", "The {noun} Keeper",
    ],
    Genre.SCIFI: [
        "Star {noun}", "The {adj} Galaxy", "Beyond {place}",
        "Chronicles of {noun}", "The {noun} Protocol", "Quantum {noun}",
        "The Mars {noun}", "Nebula {noun}", "The {adj} Station",
    ],
    Genre.MYSTERY: [
        "The {noun} Murder", "Death in {place}", "The {adj} Detective",
        "Case of the {adj} {noun}", "Murder at {place}", "The {noun} Secret",
        "Silent {noun}", "The Last {noun}", "Shadows of {noun}",
    ],
    Genre.ROMANCE: [
        "Love in {place}", "The {adj} Heart", "When Hearts {verb}",
        "Forever {adj}", "A {noun} to Remember", "The {noun} of Love",
        "Midnight {noun}", "Summer {noun}", "The {adj} Promise",
    ],
    Genre.SELF_HELP: [
        "The {adj} Mind", "{num} Ways to {verb}", "Mastering {noun}",
        "The Power of {noun}", "Unlocking Your {noun}", "The {noun} Habit",
        "Think {adj}", "Atomic {noun}", "The {adj} You",
    ],
    Genre.BIOGRAPHY: [
        "The Life of {name}", "{name}: A Story", "Becoming {name}",
        "My {adj} Journey", "The {noun} Years", "Walking with {noun}",
        "Against All {noun}", "From {noun} to {noun}", "The {adj} Path",
    ],
    Genre.HISTORY: [
        "The {adj} Empire", "Rise and Fall of {noun}", "The {place} Wars",
        "A History of {noun}", "The {adj} Century", "Empires of {noun}",
        "The World in {noun}", "Legacy of {noun}", "The {adj} Revolution",
    ],
    Genre.BUSINESS: [
        "The {adj} Leader", "{noun} Strategy", "Building {noun}",
        "The {noun} Mindset", "From Zero to {noun}", "The Art of {noun}",
        "Scaling {noun}", "The {adj} Startup", "Leadership {noun}",
    ],
    Genre.FANTASY: [
        "The {adj} Kingdom", "Realm of {noun}", "The {noun} Chronicles",
        "Dragon's {noun}", "The {adj} Sword", "Shadows of {place}",
        "The Last {noun}", "Crown of {noun}", "The {adj} Prophecy",
    ],
    Genre.THRILLER: [
        "The {noun} Conspiracy", "Dead {noun}", "The {adj} Target",
        "Run from {noun}", "The {noun} Code", "Night {noun}",
        "The {adj} Chase", "Point of {noun}", "The Final {noun}",
    ],
}

ADJECTIVES = [
    "Hidden", "Lost", "Silent", "Dark", "Golden", "Silver", "Broken",
    "Forgotten", "Eternal", "Sacred", "Ancient", "Modern", "Wild",
    "Quiet", "Brave", "Fearless", "Gentle", "Fierce", "Mysterious",
    "Elegant", "Bold", "Brilliant", "Creative", "Mindful", "Strategic",
]

NOUNS = [
    "Shadow", "Light", "Dream", "Heart", "Mind", "Soul", "Path",
    "Journey", "Secret", "Truth", "Bridge", "Door", "Window", "Garden",
    "Forest", "Mountain", "Ocean", "River", "Sky", "Star", "Moon",
    "Kingdom", "Empire", "Legacy", "Fortune", "Destiny", "Horizon",
]

PLACES = [
    "Paris", "London", "New York", "Tokyo", "Rome", "Venice",
    "Barcelona", "Prague", "Vienna", "Amsterdam", "Dublin", "Edinburgh",
    "the Valley", "the Mountains", "the Sea", "the Desert", "the Forest",
]

VERBS = [
    "Collide", "Dance", "Whisper", "Dream", "Fly", "Run", "Hide",
    "Succeed", "Transform", "Grow", "Heal", "Lead", "Create", "Build",
]

NAMES = [
    "Elizabeth", "William", "Charlotte", "James", "Victoria", "Henry",
    "Catherine", "Alexander", "Maria", "Thomas", "Eleanor", "Benjamin",
]


def generate_title(genre: Genre) -> str:
    """Generate a random book title based on genre."""
    templates = TITLE_TEMPLATES.get(genre, TITLE_TEMPLATES[Genre.FICTION])
    template = random.choice(templates)

    return template.format(
        adj=random.choice(ADJECTIVES),
        noun=random.choice(NOUNS),
        place=random.choice(PLACES),
        name=random.choice(NAMES),
        verb=random.choice(VERBS),
        num=random.choice(["7", "10", "12", "21", "30", "52", "100"]),
    )


def generate_description(genre: Genre, title: str) -> str:
    """Generate a book description."""
    genre_intros = {
        Genre.FICTION: "A compelling story that explores the depths of human emotion.",
        Genre.SCIFI: "An epic journey through space and time that challenges our understanding of reality.",
        Genre.MYSTERY: "A gripping tale of suspense that will keep you guessing until the final page.",
        Genre.ROMANCE: "A heartwarming story of love, loss, and second chances.",
        Genre.SELF_HELP: "Transform your life with proven strategies and actionable insights.",
        Genre.BIOGRAPHY: "An intimate portrait of a remarkable life and its lasting impact.",
        Genre.HISTORY: "A fascinating exploration of events that shaped our world.",
        Genre.BUSINESS: "Essential insights for leaders and entrepreneurs in today's dynamic market.",
        Genre.FANTASY: "Enter a world of magic, adventure, and legendary heroes.",
        Genre.THRILLER: "A pulse-pounding adventure that will leave you breathless.",
    }

    intro = genre_intros.get(genre, genre_intros[Genre.FICTION])
    middle = fake.paragraph(nb_sentences=3)
    return f"{intro} {middle}"


def generate_isbn() -> str:
    """Generate a realistic ISBN-13."""
    prefix = "978"
    group = str(random.randint(0, 1))
    publisher = str(random.randint(10000, 99999))
    title_code = str(random.randint(100, 999))

    # Calculate check digit
    isbn_without_check = f"{prefix}{group}{publisher}{title_code}"
    total = sum(
        int(digit) * (1 if i % 2 == 0 else 3)
        for i, digit in enumerate(isbn_without_check)
    )
    check = (10 - (total % 10)) % 10

    return f"{prefix}-{group}-{publisher}-{title_code}-{check}"


def generate_books(count: int = 500) -> list[dict]:
    """Generate a list of book data dictionaries."""
    books = []
    used_isbns = set()
    used_titles = set()

    # Genre distribution (weighted towards popular genres)
    genre_weights = {
        Genre.FICTION: 80,
        Genre.MYSTERY: 60,
        Genre.ROMANCE: 50,
        Genre.THRILLER: 50,
        Genre.FANTASY: 45,
        Genre.SCIFI: 45,
        Genre.SELF_HELP: 40,
        Genre.BIOGRAPHY: 35,
        Genre.HISTORY: 30,
        Genre.BUSINESS: 35,
    }

    genres = []
    for genre, weight in genre_weights.items():
        genres.extend([genre] * weight)

    for i in range(count):
        # Generate unique ISBN
        isbn = generate_isbn()
        while isbn in used_isbns:
            isbn = generate_isbn()
        used_isbns.add(isbn)

        # Select genre
        genre = random.choice(genres)

        # Generate unique title
        title = generate_title(genre)
        attempt = 0
        while title in used_titles and attempt < 10:
            title = generate_title(genre)
            attempt += 1
        if title in used_titles:
            title = f"{title} ({i})"
        used_titles.add(title)

        # Select author
        author = random.choice(AUTHORS)

        # Generate price ($9.99 - $34.99)
        price = round(random.uniform(9.99, 34.99), 2)

        # Generate stock (some out of stock, some low)
        stock_distribution = [0] * 5 + [1, 2, 3] * 3 + list(range(5, 100))
        stock = random.choice(stock_distribution)

        # Generate rating (weighted towards higher ratings)
        rating = round(random.triangular(2.5, 5.0, 4.2), 1)
        num_reviews = random.randint(0, 5000) if rating > 3.0 else random.randint(0, 100)

        # Generate publication date (last 30 years)
        days_ago = random.randint(0, 365 * 30)
        pub_date = datetime.utcnow() - timedelta(days=days_ago)

        # Page count
        page_count = random.randint(150, 800)

        # Cover image (using picsum for placeholder)
        cover_image = f"https://picsum.photos/seed/{isbn}/200/300"

        books.append({
            "isbn": isbn,
            "title": title,
            "author": author,
            "genre": genre,
            "price": price,
            "description": generate_description(genre, title),
            "cover_image": cover_image,
            "stock_quantity": stock,
            "rating": rating,
            "num_reviews": num_reviews,
            "page_count": page_count,
            "publication_date": pub_date,
        })

    return books


async def seed_books(session, count: int = 500):
    """Seed the database with books."""
    from sqlalchemy import select

    # Check if books already exist
    result = await session.execute(select(Book).limit(1))
    if result.scalar_one_or_none():
        print("Books already seeded, skipping...")
        return

    print(f"Generating {count} books...")
    books_data = generate_books(count)

    for book_data in books_data:
        book = Book(**book_data)
        session.add(book)

    await session.commit()
    print(f"Seeded {count} books successfully!")
