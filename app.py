"""
Amazon Indie Author Finder 2026 - FIXED LINES
"""
import streamlit as st
from datetime import date, timedelta, datetime
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
import random

MIN_PUBLICATION_YEAR = 2026

USA_STATES = [
    "All USA", "Alabama", "Alaska", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "District of Columbia", "Florida",
    "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas",
    "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
    "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
    "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

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
    created_at = Column(DateTime, default=datetime.utcnow)

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    genre = Column(String(100), index=True)
    publication_date = Column(Date, nullable=False, index=True)
    publication_month = Column(String(20))
    publication_year = Column(Integer, nullable=False, index=True)
    amazon_url = Column(String(500))
    publisher = Column(String(255))
    publishing_type = Column(String(50), default="Unknown")
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
    last_run_time = Column(DateTime)
    status = Column(String(50), default="pending")

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine("sqlite:///indie_authors.db", echo=False)
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
            q = session.query(func.count(Book.id))
            q = q.filter(Book.date_found == date.today())
            return q.scalar() or 0
        finally:
            session.close()

    def get_new_this_month(self):
        session = self.get_session()
        try:
            q = session.query(func.count(Book.id))
            q = q.filter(Book.date_found >= date.today().replace(day=1))
            return q.scalar() or 0
        finally:
            session.close()

    def get_books(self, filters=None, limit=100):
        session = self.get_session()
        try:
            q = session.query(Book).options(joinedload(Book.author))
            if filters:
                if filters.get("genre"):
                    q = q.filter(Book.genre == filters["genre"])
                if filters.get("state") and filters["state"] != "All USA":
                    q = q.join(Author).filter(Author.state == filters["state"])
                if filters.get("min_indie_score"):
                    q = q.filter(Book.indie_score >= filters["min_indie_score"])
            q = q.order_by(Book.publication_date.desc()).limit(limit)
            return q.all()
        finally:
            session.close()

    def export_books(self, filters=None):
        books = self.get_books(filters, limit=10000)
        result = []
        for b in books:
            d = {}
            d["title"] = b.title
            d["author_name"] = b.author.name if b.author else "Unknown"
            d["genre"] = b.genre
            d["publication_date"] = b.publication_date.isoformat() if b.publication_date else ""
            d["indie_score"] = b.indie_score
            d["amazon_url"] = b.amazon_url or ""
            result.append(d)
        return result

    def get_discovery_history(self, limit=30):
        session = self.get_session()
        try:
            q = session.query(DailyDiscoveryLog)
            q = q.order_by(DailyDiscoveryLog.discovery_date.desc())
            return q.limit(limit).all()
        finally:
            session.close()

    def get_session_raw(self):
        return self.get_session()

GOODREADS_BOOKS = [
    {"title": "Indie Authors Guide", "author": "Sarah Martinez", "genre": "Nonfiction", "year": 2026, "rating": 4.5},
    {"title": "Shadows Forgotten", "author": "Michael Chen", "genre": "Fantasy", "year": 2026, "rating": 4.3},
    {"title": "Love Time AI", "author": "Emily Thompson", "genre": "Romance", "year": 2026, "rating": 4.6},
    {"title": "Last Detective", "author": "James OBrien", "genre": "Mystery", "year": 2026, "rating": 4.4},
    {"title": "Beyond Stars", "author": "David Williams", "genre": "Sci-Fi", "year": 2026, "rating": 4.7},
    {"title": "Healers Journey", "author": "Jessica Anderson", "genre": "Fantasy", "year": 2026, "rating": 4.5},
    {"title": "Midnight Secrets", "author": "Robert Garcia", "genre": "Thriller", "year": 2026, "rating": 4.2},
    {"title": "Self Publishing", "author": "Amanda Lee", "genre": "Nonfiction", "year": 2026, "rating": 4.8},
    {"title": "Dragons Legacy", "author": "Chris Brown", "genre": "Fantasy", "year": 2026, "rating": 4.4},
    {"title": "Indie Marketing", "author": "Nicole Taylor", "genre": "Nonfiction", "year": 2026, "rating": 4.6}
]

def add_goodreads_books():
    db = DatabaseManager()
    session = db.get_session_raw()
    count = 0

    for bd in GOODREADS_BOOKS:
        name = bd["author"]
        ex = session.query(Author).filter(func.lower(Author.name) == func.lower(name)).first()

        if not ex:
            a = Author(name=name, website=None, email=None, country="USA")
            session.add(a)
            session.commit()
            aid = a.id
        else:
            aid = ex.id

        pd_date = date(bd["year"], 6, 1)
        score = int(bd["rating"] * 20)

        b = Book(
            title=bd["title"],
            author_id=aid,
            genre=bd["genre"],
            publication_date=pd_date,
            publication_month="June",
            publication_year=pd_date.year,
            amazon_url="https://amazon.com",
            publisher="Indie",
            publishing_type="Self-Published",
            source_url="https://goodreads.com",
            date_found=date.today(),
            first_seen=date.today(),
            last_checked=date.today(),
            verification_status="Verified Indie",
            indie_score=score
        )

        session.add(b)
        session.commit()
        count += 1

    session.close()
    return count

def add_sample_data():
    db = DatabaseManager()
    session = db.get_session_raw()

    genres = ["Fantasy", "Sci-Fi", "Mystery", "Romance", "Thriller"]
    fnames = ["James", "Sarah", "Michael", "Emily", "David"]
    lnames = ["Smith", "Johnson", "Williams", "Brown", "Jones"]

    for i in range(50):
        fn = random.choice(fnames)
        ln = random.choice(lnames)
        aname = fn + " " + ln

        ex = session.query(Author).filter(func.lower(Author.name) == func.lower(aname)).first()

        if not ex:
            # Build website, email, instagram step by step
            base = fn.lower() + ln.lower()
            ws = base + "books.com"
            em = "contact@" + ws
            ig = "@" + base

            a = Author(
                name=aname,
                website=ws,
                email=em,
                instagram=ig,
                state=random.choice(USA_STATES[1:]),
                country="USA",
                created_at=datetime.utcnow()
            )
            session.add(a)
            session.commit()
            aid = a.id
        else:
            aid = ex.id

        genre = random.choice(genres)
        days = random.randint(0, 250)
        pd_date = date(2026, 1, 1) + timedelta(days=days)
        score = random.randint(50, 95)

        if score >= 80:
            vstatus = "Verified Indie"
            ptype = "Self-Published"
        elif score >= 60:
            vstatus = "Likely Indie"
            ptype = "Independent"
        else:
            vstatus = "Needs Review"
            ptype = "Small Press"

        rand_num = random.randint(100000000, 999999999)
        amz = "https://amazon.com/dp/B" + str(rand_num)

        b = Book(
            title="Book " + str(i+1),
            author_id=aid,
            genre=genre,
            publication_date=pd_date,
            publication_month=pd_date.strftime("%B"),
            publication_year=pd_date.year,
            amazon_url=amz,
            publisher="Indie",
            publishing_type=ptype,
            source_url="https://goodreads.com",
            date_found=date.today(),
            first_seen=date.today(),
            last_checked=date.today(),
            verification_status=vstatus,
            indie_score=score
        )

        session.add(b)
        session.commit()

    session.close()
    return 50

st.set_page_config(page_title="Indie Author Finder", page_icon="📚", layout="wide")

with st.sidebar:
    st.markdown("### 📚 Menu")
    page = st.radio("Go to", ["Dashboard", "Add Sample", "Goodreads"], label_visibility="collapsed")
    st.divider()
    db = DatabaseManager()
    st.metric("Books", db.count_books())
    st.metric("Authors", db.count_authors())

if page == "Dashboard":
    st.title("📚 Indie Author Finder 2026")

    db = DatabaseManager()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("📚 Books", db.count_books())
    with c2: st.metric("✍️ Authors", db.count_authors())
    with c3: st.metric("🆕 Today", db.get_new_today())
    with c4: st.metric("📅 Month", db.get_new_this_month())

    st.divider()

    with st.sidebar:
        search = st.text_input("Search Title")
        genre_list = ["All", "Fantasy", "Sci-Fi", "Mystery", "Romance", "Thriller"]
        genre_f = st.selectbox("Genre", genre_list)
        state_f = st.selectbox("State", USA_STATES)
        min_sc = st.slider("Min Score", 0, 100, 0)

    f = {}
    if search: f["search_title"] = search
    if genre_f != "All": f["genre"] = genre_f
    if state_f != "All USA": f["state"] = state_f
    if min_sc > 0: f["min_indie_score"] = min_sc

    books = db.get_books(f, limit=50)
    st.markdown(f"### Books ({len(books)})")

    if not books:
        st.info("No books yet. Add sample data!")
    else:
        for bk in books:
            with st.container():
                c1, c2 = st.columns([1, 5])
                with c1: st.markdown("📖")
                with c2:
                    st.markdown(f"### {bk.title}")
                    an = bk.author.name if bk.author else "Unknown"
                    st.markdown(f"**Author:** {an}")
                    st.markdown(f"**Genre:** {bk.genre or "N/A"}")
                    st.markdown(f"**Date:** {bk.publication_date}")
                    if bk.author and bk.author.state:
                        st.markdown(f"📍 {bk.author.state}")
                    sc = bk.indie_score
                    em = "🟢" if sc >= 80 else "🟡" if sc >= 50 else "🔴"
                    st.markdown(f"{em} Score: {sc}")
                    if bk.amazon_url:
                        st.link_button("View", bk.amazon_url)
                st.divider()

    if st.button("Export CSV"):
        data = db.export_books(f)
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False)
        st.download_button("Download", data=csv, file_name="books.csv", mime="text/csv")

elif page == "Add Sample":
    st.markdown("### 🌱 Add Sample Data")
    db = DatabaseManager()
    st.info(f"Current: {db.count_books()} books")

    if st.button("Add 50 Books", type="primary"):
        cnt = add_sample_data()
        st.success(f"Added {cnt} books!")
        st.balloons()

elif page == "Goodreads":
    st.markdown("### 📚 Goodreads Books")

    for bk in GOODREADS_BOOKS:
        st.markdown(f"**{bk["title"]}** - {bk["author"]} ⭐{bk["rating"]}")

    if st.button(f"Add {len(GOODREADS_BOOKS)} Books", type="primary"):
        cnt = add_goodreads_books()
        st.success(f"Added {cnt} books!")
        st.balloons()

st.divider()
st.markdown("v6.2 Fixed")
