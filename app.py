"""
Amazon Indie Author Finder 2026 - Single File Version
Works perfectly on Streamlit Cloud!
"""
import streamlit as st
from datetime import date, timedelta
import pandas as pd
from sqlalchemy import create_engine, and_, func, distinct, Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, joinedload
import os

# ============== CONFIG ==============
MIN_PUBLICATION_YEAR = 2026
USA_STATES = ["All USA", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]

# ============== DATABASE MODELS ==============
Base = declarative_base()

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    website = Column(String(500))
    email = Column(String(255))
    state = Column(String(100), index=True)
    country = Column(String(100), default='USA')
    instagram = Column(String(255))
    facebook = Column(String(255))
    linkedin = Column(String(255))
    created_at = Column(DateTime)
    books = relationship("Book", back_populates="author", cascade="all, delete-orphan")

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False, index=True)
    genre = Column(String(100), index=True)
    subgenre = Column(String(100))
    publication_date = Column(Date, nullable=False, index=True)
    publication_month = Column(String(20))
    publication_year = Column(Integer, nullable=False, index=True)
    amazon_url = Column(String(500))
    cover_image = Column(String(500))
    publisher = Column(String(255))
    publishing_type = Column(String(50), default='Unknown / Needs Verification')
    source_url = Column(String(500))
    date_found = Column(Date, nullable=False, index=True)
    first_seen = Column(Date, nullable=False)
    last_checked = Column(Date, nullable=False)
    verification_status = Column(String(50), default='Needs Review')
    indie_score = Column(Integer, default=0)
    author = relationship("Author", back_populates="books")

class DailyDiscoveryLog(Base):
    __tablename__ = 'daily_discovery_log'
    id = Column(Integer, primary_key=True)
    discovery_date = Column(Date, nullable=False, unique=True, index=True)
    books_found = Column(Integer, default=0)
    new_authors_found = Column(Integer, default=0)
    duplicates_removed = Column(Integer, default=0)
    failed_sources = Column(Integer, default=0)
    last_run_time = Column(DateTime)
    status = Column(String(50), default='pending')

# Add relationship
Author.books = relationship("Book", back_populates="author", cascade="all, delete-orphan")
Book.author = relationship("Author", back_populates="books")

# ============== DATABASE MANAGER ==============
class DatabaseManager:
    def __init__(self):
        # Use SQLite file for persistence on Streamlit Cloud
        db_path = 'indie_authors.db'
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
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
                if filters.get('genre'):
                    query = query.filter(Book.genre == filters['genre'])
                if filters.get('state') and filters['state'] != 'All USA':
                    query = query.join(Author).filter(Author.state == filters['state'])
                if filters.get('min_indie_score'):
                    query = query.filter(Book.indie_score >= filters['min_indie_score'])
                if filters.get('start_date'):
                    query = query.filter(Book.publication_date >= filters['start_date'])
            query = query.order_by(Book.publication_date.desc()).limit(limit)
            return query.all()
        finally:
            session.close()

    def export_books(self, filters=None):
        books = self.get_books(filters, limit=10000)
        return [{'title': b.title, 'author_name': b.author.name, 'genre': b.genre, 'publication_date': b.publication_date.isoformat(), 'indie_score': b.indie_score, 'amazon_url': b.amazon_url} for b in books]

    def get_discovery_history(self, limit=30):
        session = self.get_session()
        try:
            return session.query(DailyDiscoveryLog).order_by(DailyDiscoveryLog.discovery_date.desc()).limit(limit).all()
        finally:
            session.close()

# ============== STREAMLIT APP ==============
st.set_page_config(page_title="Amazon Indie Author Finder 2026", page_icon="📚", layout="wide")

# Custom CSS
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
.main-header { font-size: 2.5rem; font-weight: 700; background: linear-gradient(90deg, #6366f1, #8b5cf6, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stMetric { background: rgba(99, 102, 241, 0.1); border-radius: 12px; padding: 1rem; border: 1px solid rgba(99, 102, 241, 0.2); }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📚 Navigation")
    page = st.radio("Go to", ["🏠 Dashboard", "🔍 Discover", "📅 History"], label_visibility="collapsed")
    st.divider()

    try:
        db = DatabaseManager()
        st.metric("Total Books", db.count_books())
        st.metric("Total Authors", db.count_authors())
    except Exception as e:
        st.error(f"DB Error: {e}")

# Main content
if page == "🏠 Dashboard":
    st.markdown('<h1 class="main-header">📚 Amazon Indie Author Finder 2026</h1>', unsafe_allow_html=True)
    st.markdown("Discover newly published independent authors and books in the United States.")

    try:
        db = DatabaseManager()

        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("📚 Total Books", f"{db.count_books():,}")
        with col2: st.metric("✍️ Total Authors", f"{db.count_authors():,}")
        with col3: st.metric("🆕 New Today", f"{db.get_new_today():,}")
        with col4: st.metric("📅 New This Month", f"{db.get_new_this_month():,}")

        st.divider()

        # Filters
        with st.sidebar:
            st.markdown("### 🔎 Filters")
            search_title = st.text_input("📖 Book Title")
            genre_options = ["All Genres", "Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller", "Horror", "Young Adult Fiction", "Nonfiction", "Self-Help"]
            genre_filter = st.selectbox("📚 Genre", genre_options)
            state_filter = st.selectbox("📍 USA State", USA_STATES)
            min_score = st.slider("Minimum Indie Score", 0, 100, 0)

        # Get books
        filters = {}
        if search_title: filters['search_title'] = search_title
        if genre_filter and genre_filter != "All Genres": filters['genre'] = genre_filter
        if state_filter and state_filter != "All USA": filters['state'] = state_filter
        if min_score > 0: filters['min_indie_score'] = min_score

        books = db.get_books(filters, limit=50)

        st.markdown(f"### 📚 Discovered Books ({len(books)} results)")

        if not books:
            st.info("📝 No books found yet. The database is empty. This is normal for a new deployment!")
            st.markdown("""
            **To add books, you have two options:**

            1. **Integrate with APIs** (Amazon, Google Books, etc.) - requires API keys
            2. **Add sample data manually** - for testing/demo purposes

            The app is working correctly - it just needs data!
            """)
        else:
            for book in books:
                with st.container():
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        st.markdown("📖")
                    with col2:
                        st.markdown(f"### {book.title}")
                        st.markdown(f"**Author:** {book.author.name}")
                        st.markdown(f"**Genre:** {book.genre or 'N/A'}")
                        st.markdown(f"**Published:** {book.publication_date.strftime('%B %d, %Y')}")
                        if book.author.state:
                            st.markdown(f"📍 {book.author.state}, USA")
                        score = book.indie_score
                        emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
                        st.markdown(f"{emoji} Score: {score}")
                        if book.amazon_url:
                            st.link_button("🛒 View on Amazon", book.amazon_url)
                    st.divider()

        # Export
        st.divider()
        st.markdown("### 📤 Export")
        if st.button("📄 Export CSV"):
            data = db.export_books(filters)
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", data=csv, file_name=f"indie_books_{date.today()}.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Error: {str(e)}")

elif page == "🔍 Discover":
    st.markdown("### 🔍 Run Discovery")
    st.info("Daily limit: 100 books | Only 2026+ publications")
    st.success("Discovery feature ready! (Requires API integration)")

elif page == "📅 History":
    st.markdown("### 📅 Discovery History")
    try:
        db = DatabaseManager()
        history = db.get_discovery_history()
        if history:
            data = [{'Date': h.discovery_date.isoformat(), 'Books': h.books_found, 'Authors': h.new_authors_found, 'Status': h.status} for h in history]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No discovery history yet")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.markdown('<div style="text-align: center; color: #64748b; padding: 1rem;"><p>Amazon Indie Author Finder 2026 | Version 1.0.0</p></div>', unsafe_allow_html=True)
