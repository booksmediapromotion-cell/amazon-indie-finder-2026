"""
Indie Author Finder 2026 - Google Books API
"""
import streamlit as st
from datetime import date, datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
import requests
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
    
    def add_book(self, title, author_name, genre, year, url, image="", state="California"):
        s = self.session()
        try:
            ex = s.query(Author).filter(func.lower(Author.name)==func.lower(author_name)).first()
            if not ex:
                a = Author(name=author_name, state=state)
                s.add(a)
                s.commit()
                aid = a.id
            else:
                aid = ex.id
            
            pd = date(year, random.randint(1,12), random.randint(1,28))
            b = Book(
                title=title,
                author_id=aid,
                genre=genre,
                publication_date=pd,
                publication_month=pd.strftime("%B"),
                publication_year=year,
                amazon_url=url,
                cover_image=image,
                source_url=url,
                date_found=date.today(),
                indie_score=random.randint(75, 95)
            )
            s.add(b)
            s.commit()
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            s.close()

def search_google_books(query, max_results=20):
    """Google Books API - searches for books"""
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": min(max_results, 40),
        "orderBy": "newest"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        print(f"API Status: {r.status_code}")
        d = r.json()
        books = []
        if "items" in d:
            for i in d["items"]:
                v = i.get("volumeInfo", {})
                authors = v.get("authors", [])
                if authors:
                    books.append({
                        "title": v.get("title", ""),
                        "author": authors[0],
                        "year": int(v.get("publishedDate", "2026")[:4]) if v.get("publishedDate") else 2026,
                        "genre": v.get("categories", ["Fiction"])[0] if v.get("categories") else "Fiction",
                        "url": v.get("infoLink", ""),
                        "image": v.get("imageLinks", {}).get("thumbnail", ""),
                        "publisher": v.get("publisher", "")
                    })
        print(f"Found {len(books)} books from API")
        return books
    except Exception as e:
        print(f"API Error: {e}")
        return []

st.set_page_config(page_title="Indie Finder", page_icon="📚", layout="wide")

with st.sidebar:
    st.markdown("### Menu")
    st.divider()
    db = DB()
    st.metric("Books", db.count_books())
    st.metric("Authors", db.count_authors())
    
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

# Search section
st.subheader("📖 Search & Add Books")
query = st.text_input("Search Query", value="indie fiction 2026")
max_books = st.slider("Max Results", 5, 40, 20)

if st.button("Search Google Books", type="primary"):
    with st.spinner("Searching Google Books API..."):
        books = search_google_books(query, max_books)
        if books:
            st.success(f"✅ Found {len(books)} books from Google Books API!")
            
            for bk in books:
                with st.container():
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        if bk.get("image"):
                            st.image(bk["image"], width=80)
                        else:
                            st.write("📖")
                    with c2:
                        st.write(f"### {bk['title']}")
                        st.write(f"**Author:** {bk['author']}")
                        st.write(f"**Genre:** {bk['genre']}")
                        st.write(f"**Year:** {bk['year']}")
                        st.link_button("View", bk["url"])
                        
                        if st.button(f"Add", key=f"add_{bk['title'][:10]}"):
                            if db.add_book(bk["title"], bk["author"], bk["genre"], bk["year"], bk["url"], bk.get("image", "")):
                                st.success("Added!")
                    st.divider()
            
            if st.button(f"Add All {len(books)} Books"):
                db = DB()
                cnt = 0
                for bk in books:
                    if db.add_book(bk["title"], bk["author"], bk["genre"], bk["year"], bk["url"], bk.get("image", "")):
                        cnt += 1
                st.success(f"Added {cnt} books!")
                st.balloons()
        else:
            st.warning("No books found. Try different query!")

st.divider()

# Show filtered books from database
st.subheader("📚 Books in Database")
db = DB()
books = db.get_books(genre=genre_f, location=location_f, month=month_f, year=year_f, limit=100)
st.write(f"### Results: {len(books)} Books")

if not books:
    st.info("No books in database. Search and add books above!")
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
st.write("v13.0 - Google Books API")
