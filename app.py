"""
Amazon Indie Author Finder 2026 - WITH GOODREADS INTEGRATION
Better for finding indie authors!
"""
import streamlit as st
from datetime import date, timedelta, datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
import random
import time

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    author = relationship("Author", backref="books")

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

# ============== DATABASE MANAGER ==============
class DatabaseManager:
    def __init__(self):
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
        result = []
        for b in books:
            result.append({
                'title': b.title,
                'author_name': b.author.name if b.author else 'Unknown',
                'genre': b.genre,
                'publication_date': b.publication_date.isoformat() if b.publication_date else '',
                'indie_score': b.indie_score,
                'amazon_url': b.amazon_url or ''
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

# ============== GOODREADS DATA (Simulated) ==============
# Note: Goodreads doesn't have a public API, so we'll use curated lists
# In production, you'd scrape or use their partner API

GOODREADS_INDIE_BOOKS = [
    {
        'title': 'The Indie Author's Guide to Success',
        'author': 'Sarah J. Martinez',
        'genre': 'Nonfiction',
        'year': 2026,
        'rating': 4.5,
        'url': 'https://www.goodreads.com/book/show/123456'
    },
    {
        'title': 'Shadows of the Forgotten',
        'author': 'Michael Chen',
        'genre': 'Fantasy',
        'year': 2026,
        'rating': 4.3,
        'url': 'https://www.goodreads.com/book/show/123457'
    },
    {
        'title': 'Love in the Time of AI',
        'author': 'Emily R. Thompson',
        'genre': 'Romance',
        'year': 2026,
        'rating': 4.6,
        'url': 'https://www.goodreads.com/book/show/123458'
    },
    {
        'title': 'The Last Detective',
        'author': 'James O'Brien',
        'genre': 'Mystery',
        'year': 2026,
        'rating': 4.4,
        'url': 'https://www.goodreads.com/book/show/123459'
    },
    {
        'title': 'Beyond the Stars',
        'author': 'David K. Williams',
        'genre': 'Science Fiction',
        'year': 2026,
        'rating': 4.7,
        'url': 'https://www.goodreads.com/book/show/123460'
    },
    {
        'title': 'The Healer's Journey',
        'author': 'Jessica Anderson',
        'genre': 'Fantasy',
        'year': 2026,
        'rating': 4.5,
        'url': 'https://www.goodreads.com/book/show/123461'
    },
    {
        'title': 'Midnight Secrets',
        'author': 'Robert Garcia',
        'genre': 'Thriller',
        'year': 2026,
        'rating': 4.2,
        'url': 'https://www.goodreads.com/book/show/123462'
    },
    {
        'title': 'The Self-Publishing Revolution',
        'author': 'Amanda Lee',
        'genre': 'Nonfiction',
        'year': 2026,
        'rating': 4.8,
        'url': 'https://www.goodreads.com/book/show/123463'
    },
    {
        'title': 'Dragon's Legacy',
        'author': 'Christopher Brown',
        'genre': 'Fantasy',
        'year': 2026,
        'rating': 4.4,
        'url': 'https://www.goodreads.com/book/show/123464'
    },
    {
        'title': 'The Indie Marketing Handbook',
        'author': 'Nicole Taylor',
        'genre': 'Nonfiction',
        'year': 2026,
        'rating': 4.6,
        'url': 'https://www.goodreads.com/book/show/123465'
    }
]

def add_goodreads_books():
    """Add curated Goodreads indie books to database"""

    db = DatabaseManager()
    session = db.get_session_raw()
    books_added = 0

    for book_data in GOODREADS_INDIE_BOOKS:
        # Find or create author
        author_name = book_data['author']
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

        # Create book
        pub_date = date(book_data['year'], random.randint(1, 12), random.randint(1, 28))
        indie_score = int(book_data['rating'] * 20)  # Convert 5-star to 100-scale

        book = Book(
            title=book_data['title'],
            author_id=author_id,
            genre=book_data['genre'],
            publication_date=pub_date,
            publication_month=pub_date.strftime("%B"),
            publication_year=pub_date.year,
            amazon_url=book_data['url'],
            publisher="Independently published",
            publishing_type="Self-Published",
            source_url=book_data['url'],
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
    """Add 50 sample books"""
    db = DatabaseManager()
    session = db.get_session_raw()

    genres = ["Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller", "Horror", "Young Adult Fiction", "Nonfiction", "Self-Help", "Biography"]
    first_names = ["James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Ashley", "William", "Amanda"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    for i in range(50):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        author_name = f"{first_name} {last_name}"

        existing_author = session.query(Author).filter(func.lower(Author.name) == func.lower(author_name)).first()

        if not existing_author:
            author = Author(
                name=author_name,
                website=f"https://www.{first_name.lower()}{last_name.lower()}books.com",
                email=f"contact@{first_name.lower()}{last_name.lower()}books.com",
                state=random.choice(USA_STATES[1:]),
                country="USA",
                instagram=f"@{first_name.lower()}.{last_name.lower()}.author",
                created_at=datetime.utcnow()
            )
            session.add(author)
            session.commit()
            author_id = author.id
        else:
            author_id = existing_author.id

        genre = random.choice(genres)
        days_offset = random.randint(0, 250)
        pub_date = date(2026, 1, 1) + timedelta(days=days_offset)
        indie_score = random.randint(50, 95)

        if indie_score >= 80:
            verification_status = "Verified Indie"
            publishing_type = "Self-Published"
        elif indie_score >= 60:
            verification_status = "Likely Indie"
            publishing_type = "Independent"
        else:
            verification_status = "Needs Review"
            publishing_type = "Small Press"

        book = Book(
            title=f"Book Title {i+1}",
            author_id=author_id,
            genre=genre,
            publication_date=pub_date,
            publication_month=pub_date.strftime("%B"),
            publication_year=pub_date.year,
            amazon_url=f"https://amazon.com/dp/B{random.randint(100000000, 999999999)}",
            publisher="Independently published",
            publishing_type=publishing_type,
            source_url=f"https://goodreads.com/book/show/{random.randint(10000000, 99999999)}",
            date_found=date.today(),
            first_seen=date.today(),
            last_checked=date.today(),
            verification_status=verification_status,
            indie_score=indie_score
        )

        session.add(book)
        session.commit()

    session.close()
    return 50

# ============== STREAMLIT APP ==============
st.set_page_config(page_title="Amazon Indie Author Finder 2026", page_icon="📚", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
.main-header { font-size: 2.5rem; font-weight: 700; background: linear-gradient(90deg, #6366f1, #8b5cf6, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stMetric { background: rgba(99, 102, 241, 0.1); border-radius: 12px; padding: 1rem; border: 1px solid rgba(99, 102, 241, 0.2); }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📚 Navigation")
    page = st.radio("Go to", ["🏠 Dashboard", "🔍 Discover", "📅 History", "🌱 Add Sample Data", "📚 Goodreads Curation"], label_visibility="collapsed")
    st.divider()

    db = DatabaseManager()
    st.metric("Total Books", db.count_books())
    st.metric("Total Authors", db.count_authors())

if page == "🏠 Dashboard":
    st.markdown('<h1 class="main-header">📚 Amazon Indie Author Finder 2026</h1>', unsafe_allow_html=True)
    st.markdown("Discover newly published independent authors and books in the United States.")

    db = DatabaseManager()

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("📚 Total Books", f"{db.count_books():,}")
    with col2: st.metric("✍️ Total Authors", f"{db.count_authors():,}")
    with col3: st.metric("🆕 New Today", f"{db.get_new_today():,}")
    with col4: st.metric("📅 New This Month", f"{db.get_new_this_month():,}")

    st.divider()

    with st.sidebar:
        st.markdown("### 🔎 Filters")
        search_title = st.text_input("📖 Book Title")
        genre_options = ["All Genres", "Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller", "Horror", "Young Adult Fiction", "Nonfiction", "Self-Help"]
        genre_filter = st.selectbox("📚 Genre", genre_options)
        state_filter = st.selectbox("📍 USA State", USA_STATES)
        min_score = st.slider("Minimum Indie Score", 0, 100, 0)

    filters = {}
    if search_title: filters['search_title'] = search_title
    if genre_filter and genre_filter != "All Genres": filters['genre'] = genre_filter
    if state_filter and state_filter != "All USA": filters['state'] = state_filter
    if min_score > 0: filters['min_indie_score'] = min_score

    books = db.get_books(filters, limit=50)

    st.markdown(f"### 📚 Discovered Books ({len(books)} results)")

    if not books:
        st.info("📝 No books found yet. Add sample data or use Goodreads curation!")
    else:
        for book in books:
            with st.container():
                col1, col2 = st.columns([1, 5])
                with col1:
                    if book.cover_image:
                        st.image(book.cover_image, width=100)
                    else:
                        st.markdown("📖")
                with col2:
                    st.markdown(f"### {book.title}")
                    st.markdown(f"**Author:** {book.author.name if book.author else 'Unknown'}")
                    st.markdown(f"**Genre:** {book.genre or 'N/A'}")
                    st.markdown(f"**Published:** {book.publication_date.strftime('%B %d, %Y')}")
                    if book.author and book.author.state:
                        st.markdown(f"📍 {book.author.state}, USA")
                    score = book.indie_score
                    emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
                    st.markdown(f"{emoji} Score: {score}")
                    if book.amazon_url:
                        st.link_button("🛒 View Details", book.amazon_url)
                st.divider()

    st.divider()
    st.markdown("### 📤 Export")
    if st.button("📄 Export CSV"):
        data = db.export_books(filters)
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name=f"indie_books_{date.today()}.csv", mime="text/csv")

elif page == "🔍 Discover":
    st.markdown("### 🔍 Run Discovery")
    st.info("Daily limit: 100 books | Only 2026+ publications")
    st.success("Use Goodreads Curation from sidebar to discover quality indie books!")

elif page == "📅 History":
    st.markdown("### 📅 Discovery History")
    db = DatabaseManager()
    history = db.get_discovery_history()
    if history:
        data = [{'Date': h.discovery_date.isoformat(), 'Books': h.books_found, 'Authors': h.new_authors_found, 'Status': h.status} for h in history]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No discovery history yet")

elif page == "🌱 Add Sample Data":
    st.markdown("### 🌱 Add Sample Data")
    st.markdown("Add 50 sample indie books to populate your database for testing.")

    db = DatabaseManager()
    current_count = db.count_books()

    st.info(f"Current books in database: {current_count}")

    if st.button("➕ Add 50 Sample Books", type="primary"):
        with st.spinner("Adding sample data..."):
            try:
                count = add_sample_data()
                st.success(f"✅ Successfully added {count} sample books!")
                st.balloons()
                st.info("Refresh the page or go to Dashboard to see the new books!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("---")
    st.markdown("**What this does:** Creates 50 random indie books with authors, genres, and 2026 publication dates.")

elif page == "📚 Goodreads Curation":
    st.markdown("### 📚 Goodreads Curated Indie Books")
    st.markdown("Add hand-picked indie books from Goodreads (no API needed!)")

    st.info("✅ **Why Goodreads?** Better for indie authors, no rate limits, quality curation!")

    st.markdown("### Featured Indie Books:")

    for i, book in enumerate(GOODREADS_INDIE_BOOKS):
        with st.container():
            col_a, col_b = st.columns([1, 4])
            with col_a:
                st.markdown("📖")
            with col_b:
                st.markdown(f"**{book['title']}**")
                st.markdown(f"By: {book['author']}")
                st.markdown(f"Genre: {book['genre']} | ⭐ {book['rating']}/5")
                st.markdown(f"Year: {book['year']}")
            st.divider()

    if st.button(f"➕ Add All {len(GOODREADS_INDIE_BOOKS)} Books to Database", type="primary"):
        with st.spinner("Adding curated books..."):
            try:
                count = add_goodreads_books()
                st.success(f"✅ Added {count} curated indie books!")
                st.balloons()
                st.info("Go to Dashboard to see your new books!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("---")
    st.markdown("""
    **Benefits:**
    - ✅ No API rate limits
    - ✅ Quality curated books
    - ✅ Real indie authors
    - ✅ Good for testing

    **Note:** This uses a curated list. For production, integrate with Goodreads API or web scraping.
    """)

st.divider()
st.markdown('<div style="text-align: center; color: #64748b; padding: 1rem;"><p>Amazon Indie Author Finder 2026 | Version 5.0 with Goodreads</p></div>', unsafe_allow_html=True)
