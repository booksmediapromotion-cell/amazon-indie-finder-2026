"""
Amazon Indie Author Finder 2026 - CLEAN VERSION
"""
import streamlit as st
from datetime import date, timedelta, datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
import random

MIN_PUBLICATION_YEAR = 2026
USA_STATES = ["All USA", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]

Base = declarative_base()

class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    website = Column(String(500))
    email = Column(String(255))
    state = Column(String(100), index=True)
    country = Column(String(100), default="USA")
    instagram = Column(String(255))
    facebook = Column(String(255))
    linkedin = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False, index=True)
    genre = Column(String(100), index=True)
    subgenre = Column(String(100))
    publication_date = Column(Date, nullable=False, index=True)
    publication_month = Column(String(20))
    publication_year = Column(Integer, nullable=False, index=True)
    amazon_url = Column(String(500))
    cover_image = Column(String(500))
    publisher = Column(String(255))
    publishing_type = Column(String(50), default="Unknown / Needs Verification")
    source_url = Column(String(500))
    date_found = Column(Date, nullable=False, index=True)
    first_seen = Column(Date, nullable=False)
    last_checked = Column(Date, nullable=False)
    verification_status = Column(String(50), default="Needs Review")
    indie_score = Column(Integer, default=0)
    author = relationship("Author", backref="books")

class DailyDiscoveryLog(Base):
    __tablename__ = "daily_discovery_log"
    id = Column(Integer, primary_key=True)
    discovery_date = Column(Date, nullable=False, unique=True, index=True)
    books_found = Column(Integer, default=0)
    new_authors_found = Column(Integer, default=0)
    duplicates_removed = Column(Integer, default=0)
    failed_sources = Column(Integer, default=0)
    last_run_time = Column(DateTime)
    status = Column(String(50), default="pending")

class DatabaseManager:
    def __init__(self):
        db_path = "indie_authors.db"
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def count_authors(self):
        session = self.get_session()
        try:
            return session.query(func.count(Author.id)).scalar() or 0
        finally:
            session.close()

    def count_books(self):
        session = self.get_session()
        try:
            return session.query(func.count(Book.id)).scalar() or 0
        finally:
            session.close()

    def get_new_today(self):
        session = self.get_session()
        try:
            return session.query(func.count(Book.id)).filter(Book.date_found == date.today()).scalar() or 0
        finally:
            session.close()

    def get_new_this_month(self):
        session = self.get_session()
        try:
            return session.query(func.count(Book.id)).filter(Book.date_found >= date.today().replace(day=1)).scalar() or 0
        finally:
            session.close()

    def get_books(self, filters=None, limit=100):
        session = self.get_session()
        try:
            query = session.query(Book).options(joinedload(Book.author))
            if filters:
                if filters.get("genre"):
                    query = query.filter(Book.genre == filters["genre"])
                if filters.get("state") and filters["state"] != "All USA":
                    query = query.join(Author).filter(Author.state == filters["state"])
                if filters.get("min_indie_score"):
                    query = query.filter(Book.indie_score >= filters["min_indie_score"])
                if filters.get("start_date"):
                    query = query.filter(Book.publication_date >= filters["start_date"])
            query = query.order_by(Book.publication_date.desc()).limit(limit)
            return query.all()
        finally:
            session.close()

    def export_books(self, filters=None):
        books = self.get_books(filters, limit=10000)
        result = []
        for b in books:
            result.append({
                "title": b.title,
                "author_name": b.author.name if b.author else "Unknown",
                "genre": b.genre,
                "publication_date": b.publication_date.isoformat() if b.publication_date else "",
                "indie_score": b.indie_score,
                "amazon_url": b.amazon_url or ""
            })
        return result

    def get_discovery_history(self, limit=30):
        session = self.get_session()
        try:
            return session.query(DailyDiscoveryLog).order_by(DailyDiscoveryLog.discovery_date.desc()).limit(limit).all()
        finally:
            session.close()

    def get_session_raw(self):
        return self.get_session()

GOODREADS_INDIE_BOOKS = [
    {"title": "The Indie Authors Guide", "author": "Sarah Martinez", "genre": "Nonfiction", "year": 2026, "rating": 4.5, "url": "https://goodreads.com/book/1"},
    {"title": "Shadows of the Forgotten", "author": "Michael Chen", "genre": "Fantasy", "year": 2026, "rating": 4.3, "url": "https://goodreads.com/book/2"},
    {"title": "Love in the Time of AI", "author": "Emily Thompson", "genre": "Romance", "year": 2026, "rating": 4.6, "url": "https://goodreads.com/book/3"},
    {"title": "The Last Detective", "author": "James OBrien", "genre": "Mystery", "year": 2026, "rating": 4.4, "url": "https://goodreads.com/book/4"},
    {"title": "Beyond the Stars", "author": "David Williams", "genre": "Science Fiction", "year": 2026, "rating": 4.7, "url": "https://goodreads.com/book/5"},
    {"title": "The Healers Journey", "author": "Jessica Anderson", "genre": "Fantasy", "year": 2026, "rating": 4.5, "url": "https://goodreads.com/book/6"},
    {"title": "Midnight Secrets", "author": "Robert Garcia", "genre": "Thriller", "year": 2026, "rating": 4.2, "url": "https://goodreads.com/book/7"},
    {"title": "Self Publishing Revolution", "author": "Amanda Lee", "genre": "Nonfiction", "year": 2026, "rating": 4.8, "url": "https://goodreads.com/book/8"},
    {"title": "Dragons Legacy", "author": "Christopher Brown", "genre": "Fantasy", "year": 2026, "rating": 4.4, "url": "https://goodreads.com/book/9"},
    {"title": "Indie Marketing Handbook", "author": "Nicole Taylor", "genre": "Nonfiction", "year": 2026, "rating": 4.6, "url": "https://goodreads.com/book/10"}
]

def add_goodreads_books():
    db = DatabaseManager()
    session = db.get_session_raw()
    books_added = 0

    for book_data in GOODREADS_INDIE_BOOKS:
        author_name = book_data["author"]
        existing_author = session.query(Author).filter(func.lower(Author.name) == func.lower(author_name)).first()

        if not existing_author:
            author = Author(
                name=author_name,
                website=None,
                email=None,
                state=random.choice(USA_STATES[1:]) if random.random() > 0.5 else None,
                country="USA",
                created_at=datetime.utcnow()
            )
            session.add(author)
            session.commit()
            author_id = author.id
        else:
            author_id = existing_author.id

        pub_date = date(book_data["year"], random.randint(1, 12), 1)
        indie_score = int(book_data["rating"] * 20)

        book = Book(
            title=book_data["title"],
            author_id=author_id,
            genre=book_data["genre"],
            publication_date=pub_date,
            publication_month=pub_date.strftime("%B"),
            publication_year=pub_date.year,
            amazon_url=book_data["url"],
            publisher="Independently published",
            publishing_type="Self-Published",
            source_url=book_data["url"],
            date_found=date.today(),
            first_seen=date.today(),
            last_checked=date.today(),
            verification_status="Verified Indie",
            indie_score=indie_score
        )

        session.add(book)
        session.commit()
        books_added += 1

    session.close()
    return books_added

def add_sample_data():
    db = DatabaseManager()
    session = db.get_session_raw()
    genres = ["Fantasy", "Sci-Fi", "Mystery", "Romance", "Thriller", "Horror", "YA Fiction", "Nonfiction", "Self-Help", "Biography"]
    first_names = ["James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Ashley", "William", "Amanda"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    for i in range(50):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        author_name = f"{first_name} {last_name}"

        existing_author = session.query(Author).filter(func.lower(Author.name) == func.lower(author_name)).first()

        if not existing_author:
            website = f"https://{first_name.lower()}{last_name.lower()}books.com"
            email = f"contact@{first_name.lower()}{last_name.lower()}books.c
