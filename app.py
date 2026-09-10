"""
Indie Author Finder 2026 - Clean Version
"""
import streamlit as st
from datetime import date, datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
import requests
import random

USA_STATES = ["All USA", "California", "Texas", "New York", "Florida"]

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

    def get_books(self, limit=50):
        s = self.session()
        try:
            return s.query(Book).options(joinedload(Book.author)).order_by(Book.publication_date.desc()).limit(limit).all()
        finally:
            s.close()

    def add_book(self, title, author_name, genre, year, url):
        s = self.session()
        try:
            ex = s.query(Author).filter(func.lower(Author.name)==func.lower(author_name)).first()
            if not ex:
                a = Author(name=author_name, state="California")
                s.add(a)
                s.commit()
                aid = a.id
            else:
                aid = ex.id

            pd = date(year, random.randint(1,12), 1)
            b = Book(
                title=title,
                author_id=aid,
                genre=genre,
                publication_date=pd,
                publication_month=pd.strftime("%B"),
                publication_year=year,
                amazon_url=url,
                source_url=url,
                date_found=date.today()
            )
            s.add(b)
            s.commit()
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            s.close()

def search_google(q, max_res=20):
    url = "https://www.googleapis.com/books/v1/volumes"
    p = {"q": q, "maxResults": min(max_res,40), "orderBy": "newest"}
    try:
        r = requests.get(url, params=p, timeout=10)
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
                        "image": v.get("imageLinks", {}).get("thumbnail", "")
                    })
        return books
    except:
        return []

st.set_page_config(page_title="Indie Finder", page_icon="📚", layout="wide")

with st.sidebar:
    st.markdown("### Menu")
    pg = st.radio("Page", ["Dashboard", "Search"], label_visibility="collapsed")
    st.divider()
    db = DB()
    st.metric("Books", db.count_books())

if pg == "Dashboard":
    st.title("📚 Indie Author Finder")
    db = DB()
    st.metric("Total Books", db.count_books())
    st.divider()

    books = db.get_books(50)
    st.write(f"### Books ({len(books)})")

    if not books:
        st.info("No books. Go to Search!")
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
                    st.write(f"**Author:** {b.author.name if b.author else '?'}")
                    st.write(f"**Genre:** {b.genre}")
                    st.write(f"**Date:** {b.publication_date}")
                    if b.source_url:
                        st.link_button("View", b.source_url)
                st.divider()

elif pg == "Search":
    st.title("🔍 Search Books")

    q = st.text_input("Search", value="indie books 2026")
    max_b = st.slider("Max", 5, 40, 20)

    if st.button("Search", type="primary"):
        with st.spinner("Searching..."):
            books = search_google(q, max_b)
            if books:
                st.success(f"Found {len(books)} books!")
                for bk in books[:10]:
                    with st.container():
                        c1, c2 = st.columns([1, 4])
                        with c1:
                            if bk.get("image"):
                                st.image(bk["image"], width=80)
                            else:
                                st.write("📖")
                        with c2:
                            st.write(f"**{bk['title']}**")
                            st.write(f"By: {bk['author']}")
                            st.link_button("View", bk["url"])
                        st.divider()

                if st.button(f"Add All {len(books)} Books"):
                    db = DB()
                    cnt = 0
                    for bk in books:
                        if db.add_book(bk["title"], bk["author"], bk["genre"], bk["year"], bk["url"]):
                            cnt += 1
                    st.success(f"Added {cnt} books!")
                    st.balloons()
            else:
                st.warning("No books found")

    st.divider()
    db = DB()
    if st.button("Clear All Data"):
        db.clear()
        st.success("Cleared! Refresh page")

st.divider()
st.write("v10.0")
