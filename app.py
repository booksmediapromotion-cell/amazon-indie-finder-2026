"""
Indie Author Finder 2026 - Filters Only
"""
import streamlit as st
from datetime import date, datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
import random

USA_STATES = ["All Locations", "California", "Texas", "New York", "Florida", "Washington", "Oregon", "Colorado", "North Carolina", "Georgia"]
GENRES = ["All Genres", "Fiction", "Nonfiction", "Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller", "Self-Help", "Business", "Biography", "History"]
MONTHS = ["All Months", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
YEARS = ["All Years", "2026", "2025", "2024", "2023", "2022"]

Base = declarative_base()

class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    state = Column(String(100))
    country = Column(String(100), default="USA")
    created_at = Column(DateTime, default=datetime.utcnow)

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    genre = Column(String(100))
    publication_date = Column(Date, nullable=False)
    publication_month = Column(String(20))
    publication_year = Column(Integer, nullable=False)
    amazon_url = Column(String(500))
    cover_image = Column(String(500))
    publisher = Column(String(255))
    source_url = Column(String(500))
    date_found = Column(Date, nullable=False)
    indie_score = Column(Integer, default=85)
    author = relationship("Author", backref="books")

class DB:
    def __init__(self):
        self.engine = create_engine("sqlite:///indie_authors.db")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def session(self):
        return self.Session()

    def count_books(self):
        s = self.session()
        try:
            return s.query(func.count(Book.id)).scalar() or 0
        finally:
            s.close()

    def count_authors(self):
        s = self.session()
        try:
            return s.query(func.count(Author.id)).scalar() or 0
        finally:
            s.close()

    def clear(self):
        s = self.session()
        try:
            s.query(Book).delete()
            s.query(Author).delete()
            s.commit()
        finally:
            s.close()

    def get_books(self, genre="All Genres", location="All Locations", month="All Months", year="All Years", limit=100):
        s = self.session()
        try:
            q = s.query(Book).options(joinedload(Book.author))

            if genre != "All Genres":
                q = q.filter(Book.genre == genre)

            if location != "All Locations":
                q = q.join(Author).filter(Author.state == location)

            if month != "All Months":
                q = q.filter(Book.publication_month == month)

            if year != "All Years":
                q = q.filter(Book.publication_year == int(year))

            q = q.order_by(Book.publication_date.desc()).limit(limit)
            return q.all()
        finally:
            s.close()

    def add_sample_books(self):
        s = self.session()
        try:
            if s.query(func.count(Book.id)).scalar() > 0:
                return 0

            genres = ["Fiction", "Nonfiction", "Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller", "Self-Help", "Business", "Biography"]
            locations = ["California", "Texas", "New York", "Florida", "Washington", "Oregon", "Colorado", "North Carolina", "Georgia"]
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

            titles = [
                "The Silent Echo", "Beyond the Horizon", "Midnight Dreams", "The Last Chapter",
                "Hidden Truths", "Morning Light", "The Forgotten Path", "Endless Journey",
                "Shadows Within", "The Breaking Point", "Untold Stories", "The Final Word",
                "Between Worlds", "The Turning Tide", "Lost and Found", "The Quiet Storm",
                "Rising Sun", "The Open Road", "Deep Waters", "The Golden Hour"
            ]

            authors = [
                "Sarah Mitchell", "James Cooper", "Emily Rose", "Michael Chen",
                "Jessica Adams", "David Park", "Amanda White", "Robert Taylor",
                "Lauren Green", "Thomas Brown", "Nicole Davis", "Christopher Lee",
                "Melissa Hall", "Daniel Wilson", "Rachel Moore", "Kevin Anderson"
            ]

            for i in range(50):
                author_name = random.choice(authors)
                ex = s.query(Author).filter(func.lower(Author.name)==func.lower(author_name)).first()
                if not ex:
                    a = Author(name=author_name, state=random.choice(locations))
                    s.add(a)
                    s.commit()
                    aid = a.id
                else:
                    aid = ex.id

                genre = random.choice(genres)
                year = random.choice([2026, 2025, 2024, 2023])
                month = random.choice(months)
                month_num = months.index(month) + 1
                pd = date(year, month_num, random.randint(1, 28))

                b = Book(
                    title=random.choice(titles) + f" #{i+1}",
                    author_id=aid,
                    genre=genre,
                    publication_date=pd,
                    publication_month=month,
                    publication_year=year,
                    amazon_url=f"https://amazon.com/book{i}",
                    source_url=f"https://amazon.com/book{i}",
                    date_found=date.today(),
                    indie_score=random.randint(75, 95)
                )
                s.add(b)

            s.commit()
            return 50
        except Exception as e:
            print(e)
            return 0
        finally:
            s.close()

st.set_page_config(page_title="Indie Finder", page_icon="📚", layout="wide")

with st.sidebar:
    st.markdown("### Menu")
    st.divider()
    db = DB()
    st.metric("Books", db.count_books())
    st.metric("Authors", db.count_authors())

    if st.button("Add Sample Data"):
        db.add_sample_books()
        st.success("Added 50 books!")
        st.rerun()

    st.divider()
    if st.button("Clear All Data"):
        db.clear()
        st.success("Cleared!")

st.title("📚 Indie Author Finder")

# Filters
st.subheader("🔍 Filter Books")
c1, c2, c3, c4 = st.columns(4)
with c1:
    genre_f = st.selectbox("Genre", GENRES)
with c2:
    location_f = st.selectbox("Location", USA_STATES)
with c3:
    month_f = st.selectbox("Month", MONTHS)
with c4:
    year_f = st.selectbox("Year", YEARS)

st.divider()

db = DB()
books = db.get_books(genre=genre_f, location=location_f, month=month_f, year=year_f, limit=100)

st.write(f"### Results: {len(books)} Books")

if not books:
    st.info("No books found. Click 'Add Sample Data' in sidebar to see examples!")
else:
    for b in books:
        with st.container():
            c1, c2 = st.columns([1, 4])
            with c1:
                if b.cover_image:
                    st.image(b.cover_image, width=80)
                else:
                    st.write("📖")
            with c2:
                st.write(f"### {b.title}")
                st.write(f"**Author:** {b.author.name if b.author else '?'} ({b.author.state if b.author else '?'})")
                st.write(f"**Genre:** {b.genre}")
                st.write(f"**Published:** {b.publication_date.strftime('%B %d, %Y')}")
                st.write(f"**Score:** {b.indie_score}/100")
                if b.source_url:
                    st.link_button("View on Amazon", b.source_url)
            st.divider()

st.divider()
st.write("v12.0 - Filters Only")
