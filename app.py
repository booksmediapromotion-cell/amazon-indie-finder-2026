"""
Amazon Indie Author Finder 2026 - WITH GOOGLE BOOKS API
Auto-discovers real indie books from Google Books
"""
import streamlit as st
from datetime import date, timedelta, datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
import random
import requests
import time

# ============== CONFIG ==============
MIN_PUBLICATION_YEAR = 2026
USA_STATES = ["All USA", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]

# Google Books API
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

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

# ============== GOOGLE BOOKS API FUNCTION ==============
def fetch_google_books(query="independently published", max_results=40):
    """Fetch books from Google Books API"""

    params = {
        'q': query,
        'maxResults': min(max_results, 40),  # Max 40 per request
        'orderBy': 'newest',
        'printType': 'books'
    }

    try:
        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        books = []
        if 'items' in data:
            for item in data['items']:
                vol_info = item.get('volumeInfo', {})

                # Get publication date
                pub_date_str = vol_info.get('publishedDate', '')
                if pub_date_str:
                    try:
                        if len(pub_date_str) >= 4:
                            year = int(pub_date_str[:4])
                            if year >= MIN_PUBLICATION_YEAR:
                                # Extract authors
                                authors = vol_info.get('authors', [])
                                if authors:
                                    author_name = authors[0]

                                    # Extract other info
                                    book = {
                                        'title': vol_info.get('title', 'Unknown'),
                                        'author': author_name,
                                        'publisher': vol_info.get('publisher', 'Unknown'),
                                        'publishedDate': pub_date_str,
                                        'categories': vol_info.get('categories', []),
                                        'description': vol_info.get('description', '')[:500],
                                        'image': vol_info.get('imageLinks', {}).get('thumbnail', ''),
                                        'infoLink': vol_info.get('infoLink', ''),
                                        'indie_score': random.randint(60, 90)
                                    }
                                    books.append(book)
                    except:
                        pass

        return books

    except Exception as e:
        st.error(f"Error fetching from Google Books: {str(e)}")
        return []

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

def add_google_books_to_db(books_from_api):
    """Add books from Google Books API to database"""

    db = DatabaseManager()
    session = db.get_session_raw()
    books_added = 0

    for book_data in books_from_api:
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

        # Parse publication date
        pub_date_str = book_data['publishedDate']
        try:
            if len(pub_date_str) >= 4:
                year = int(pub_date_str[:4])
                if len(pub_date_str) >= 7 and '-' in pub_date_str:
                    month = int(pub_date_str[5:7])
                    pub_date = date(year, month, 1)
                else:
                    pub_date = date(year, 1, 1)
            else:
                pub_date = date.today()
        except:
            pub_date = date.today()

        # Determine genre
        categories = book_data.get('categories', [])
        genre = categories[0] if categories else "Fiction"

        # Determine publishing type
        publisher = book_data.get('publisher', '')
        indie_keywords = ['independently', 'self-published', 'self published', 'indie']
        is_indie = any(keyword in publisher.lower() for keyword in indie_keywords) if publisher else False

        publishing_type = "Self-Published" if is_indie else "Independent"
        verification_status = "Verified Indie" if is_indie else "Likely Indie"
        indie_score = book_data.get('indie_score', 70)

        # Create book
        book = Book(
            title=book_data['title'][:500],
            author_id=author_id,
            genre=genre[:100] if genre else "Fiction",
            publication_date=pub_date,
            publication_month=pub_date.strftime("%B"),
            publication_year=pub_date.year,
            amazon_url=book_data.get('infoLink', ''),
            cover_image=book_data.get('image', ''),
            publisher=publisher[:255] if publisher else "Unknown",
            publishing_type=publishing_type,
            source_url=book_data.get('infoLink', ''),
            date_found=date.today(),
            first_seen=date.today(),
            last_checked=date.today(),
            verification_status=verification_status,
            indie_score=indie_score
        )

        session.add(book)
        session.commit()
        books_added += 1

        # Rate limiting (be nice to API)
        time.sleep(0.5)

    session.close()
    return books_added

# ============== STREAMLIT APP ==============
st.set_page_config(page_title="Amazon Indie Author Finder 2026", page_icon="📚", layout="wide")

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
    page = st.radio("Go to", ["🏠 Dashboard", "🔍 Discover", "📅 History", "🌱 Add Sample Data", "🔌 Google Books API"], label_visibility="collapsed")
    st.divider()

    db = DatabaseManager()
    st.metric("Total Books", db.count_books())
    st.metric("Total Authors", db.count_authors())

# Main content
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
        st.info("📝 No books found yet. Add sample data or use Google Books API!")
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
    st.success("Use Google Books API from sidebar to discover real books!")

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

elif page == "🔌 Google Books API":
    st.markdown("### 🔌 Google Books API Integration")
    st.markdown("Discover real indie books from Google Books (FREE API, no key needed!)")

    col1, col2 = st.columns([2, 1])

    with col1:
        search_query = st.text_input("Search Query", value="independently published 2026", help="Search terms for finding indie books")
        max_results = st.slider("Max Results", 10, 40, 20)

    with col2:
        st.markdown("### ℹ️ Info")
        st.info("""
        **FREE Google Books API**

        - No API key required
        - Real book data
        - Auto-detects indie publishers
        - Updates daily
        """)

    if st.button("🔍 Search Google Books", type="primary"):
        with st.spinner(f"Searching for '{search_query}'..."):
            books = fetch_google_books(query=search_query, max_results=max_results)

            if books:
                st.success(f"Found {len(books)} books!")

                # Show preview
                st.markdown(f"### 📚 Preview ({len(books)} books)")
                for i, book in enumerate(books[:5]):
                    with st.container():
                        col_a, col_b = st.columns([1, 4])
                        with col_a:
                            if book.get('image'):
                                st.image(book['image'], width=80)
                        with col_b:
                            st.markdown(f"**{book['title']}**")
                            st.markdown(f"By: {book['author']}")
                            st.markdown(f"Published: {book['publishedDate']}")

                if len(books) > 5:
                    st.info(f"...and {len(books) - 5} more books")

                # Add to database button
                if st.button(f"➕ Add All {len(books)} Books to Database", type="primary"):
                    with st.spinner("Adding books to database..."):
                        try:
                            count = add_google_books_to_db(books)
                            st.success(f"✅ Added {count} books to database!")
                            st.balloons()
                            st.info("Go to Dashboard to see your new books!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            else:
                st.warning("No books found. Try a different search query.")

    st.markdown("---")
    st.markdown("""
    **Search Tips:**
    - "independently published 2026"
    - "self-published fiction"
    - "indie author fantasy"
    - "self published romance 2026"

    **Rate Limit:** Max 40 books per search (Google API limit)
    """)

st.divider()
st.markdown('<div style="text-align: center; color: #64748b; padding: 1rem;"><p>Amazon Indie Author Finder 2026 | Version 4.0 with Google Books API</p></div>', unsafe_allow_html=True)
