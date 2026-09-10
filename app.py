"""
Indie Author Finder 2026
Streamlit + SQLite + SQLAlchemy + Google Books API
"""

import streamlit as st
from datetime import date, datetime
from urllib.parse import quote
import requests

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Text,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Indie Author Finder",
    page_icon="📚",
    layout="wide",
)

USA_STATES = [
    "All Locations",
    "California",
    "Texas",
    "New York",
    "Florida",
    "Washington",
    "Oregon",
    "Colorado",
    "North Carolina",
    "Georgia",
]

GENRES = [
    "All Genres",
    "Fiction",
    "Nonfiction",
    "Fantasy",
    "Science Fiction",
    "Mystery",
    "Romance",
    "Thriller",
    "Self-Help",
    "Business",
    "Biography",
    "History",
]

MONTHS = [
    "All Months",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

YEARS = [
    "All Years",
    "2026",
    "2025",
    "2024",
    "2023",
    "2022",
]


# =========================================================
# DATABASE
# =========================================================

Base = declarative_base()


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    state = Column(String(100), default="")
    country = Column(String(100), default="USA")

    website = Column(String(500), default="")
    email = Column(String(255), default="")
    amazon_author_url = Column(String(500), default="")

    created_at = Column(DateTime, default=datetime.utcnow)

    books = relationship(
        "Book",
        back_populates="author",
        cascade="all, delete-orphan",
    )


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)

    # Google Books ID prevents duplicate imports
    google_book_id = Column(String(255), unique=True, nullable=True)

    title = Column(String(500), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)

    genre = Column(String(100), default="")
    publication_date = Column(Date, nullable=True)
    publication_month = Column(String(20), default="")
    publication_year = Column(Integer, nullable=True)

    google_books_url = Column(String(500), default="")
    amazon_url = Column(String(500), default="")

    cover_image = Column(String(500), default="")
    publisher = Column(String(255), default="")
    description = Column(Text, default="")

    source_url = Column(String(500), default="")
    date_found = Column(Date, default=date.today)

    indie_score = Column(Integer, default=0)

    author = relationship("Author", back_populates="books")

    __table_args__ = (
        UniqueConstraint(
            "title",
            "author_id",
            name="unique_book_author",
        ),
    )


# =========================================================
# DATABASE CLASS
# =========================================================

class DB:

    def __init__(self):
        self.engine = create_engine(
            "sqlite:///indie_authors.db",
            connect_args={"check_same_thread": False},
        )

        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

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

        except Exception:
            s.rollback()
            raise

        finally:
            s.close()

    def book_exists(self, google_book_id=None, title=None, author_name=None):

        s = self.session()

        try:

            if google_book_id:
                existing = (
                    s.query(Book)
                    .filter(Book.google_book_id == google_book_id)
                    .first()
                )

                if existing:
                    return True

            if title and author_name:

                existing = (
                    s.query(Book)
                    .join(Author)
                    .filter(
                        func.lower(Book.title) == func.lower(title),
                        func.lower(Author.name) == func.lower(author_name),
                    )
                    .first()
                )

                if existing:
                    return True

            return False

        finally:
            s.close()

    def add_book(
        self,
        title,
        author_name,
        genre,
        year=None,
        url="",
        image="",
        publisher="",
        description="",
        google_book_id=None,
        publication_date=None,
    ):

        s = self.session()

        try:

            # -------------------------------------------------
            # Check duplicate
            # -------------------------------------------------

            if google_book_id:

                existing = (
                    s.query(Book)
                    .filter(
                        Book.google_book_id == google_book_id
                    )
                    .first()
                )

                if existing:
                    return False, "Book already exists."

            # -------------------------------------------------
            # Find/create author
            # -------------------------------------------------

            author = (
                s.query(Author)
                .filter(
                    func.lower(Author.name)
                    == func.lower(author_name)
                )
                .first()
            )

            if not author:

                author = Author(
                    name=author_name,
                    state="",
                    country="USA",
                )

                s.add(author)
                s.flush()

            # -------------------------------------------------
            # Second duplicate check
            # -------------------------------------------------

            existing = (
                s.query(Book)
                .filter(
                    Book.title == title,
                    Book.author_id == author.id,
                )
                .first()
            )

            if existing:
                return False, "Book already exists."

            # -------------------------------------------------
            # Publication date
            # -------------------------------------------------

            pub_date = publication_date

            if pub_date is None and year:
                try:
                    pub_date = date(int(year), 1, 1)
                except Exception:
                    pub_date = None

            publication_month = ""

            if pub_date:
                publication_month = pub_date.strftime("%B")

            # -------------------------------------------------
            # Indie score
            #
            # We do NOT generate a fake random score.
            # Google Books alone cannot prove self-publishing.
            # -------------------------------------------------

            score = calculate_indie_score(
                publisher=publisher
            )

            # -------------------------------------------------
            # Create book
            # -------------------------------------------------

            book = Book(
                google_book_id=google_book_id,
                title=title,
                author_id=author.id,
                genre=genre,
                publication_date=pub_date,
                publication_month=publication_month,
                publication_year=(
                    pub_date.year
                    if pub_date
                    else year
                ),
                google_books_url=url,
                amazon_url="",
                cover_image=image,
                publisher=publisher,
                description=description,
                source_url=url,
                date_found=date.today(),
                indie_score=score,
            )

            s.add(book)
            s.commit()

            return True, "Book added successfully."

        except Exception as e:

            s.rollback()

            return False, str(e)

        finally:
            s.close()

    def get_books(
        self,
        genre="All Genres",
        location="All Locations",
        month="All Months",
        year="All Years",
        limit=100,
    ):

        s = self.session()

        try:

            q = (
                s.query(Book)
                .options(joinedload(Book.author))
            )

            if genre != "All Genres":

                q = q.filter(
                    Book.genre == genre
                )

            if location != "All Locations":

                q = (
                    q.join(Book.author)
                    .filter(
                        Author.state == location
                    )
                )

            if month != "All Months":

                q = q.filter(
                    Book.publication_month == month
                )

            if year != "All Years":

                q = q.filter(
                    Book.publication_year == int(year)
                )

            q = (
                q.order_by(
                    Book.publication_date.desc()
                )
                .limit(limit)
            )

            return q.all()

        finally:
            s.close()


# =========================================================
# INDIE SCORE
# =========================================================

def calculate_indie_score(publisher=""):

    """
    This is only a basic publisher-based score.
    It does NOT prove an author is self-published.
    """

    if not publisher:
        return 50

    publisher_lower = publisher.lower()

    large_publishers = [
        "penguin",
        "random house",
        "harpercollins",
        "simon & schuster",
        "hachette",
        "macmillan",
        "scholastic",
        "oxford university press",
        "cambridge university press",
    ]

    for publisher_name in large_publishers:

        if publisher_name in publisher_lower:
            return 20

    independent_terms = [
        "independent",
        "publishing",
        "press",
        "books",
        "publishing house",
    ]

    for term in independent_terms:

        if term in publisher_lower:
            return 65

    return 50


# =========================================================
# DATE PARSER
# =========================================================

def parse_publication_date(value):

    if not value:
        return None

    value = str(value).strip()

    formats = [
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                value,
                fmt,
            ).date()

            return parsed

        except ValueError:
            continue

    return None


# =========================================================
# GOOGLE BOOKS API
# =========================================================

def fetch_books_from_api(
    genre="Fiction",
    year=2026,
    max_results=20,
):

    url = "https://www.googleapis.com/books/v1/volumes"

    query = f"{genre} books {year}"

    params = {
        "q": query,
        "maxResults": min(max_results, 40),
        "orderBy": "newest",
        "printType": "books",
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20,
            headers={
                "User-Agent": "IndieAuthorFinder/2026"
            },
        )

        response.raise_for_status()

        data = response.json()

        books = []

        for item in data.get("items", []):

            volume_info = item.get(
                "volumeInfo",
                {}
            )

            title = volume_info.get(
                "title",
                ""
            ).strip()

            authors = volume_info.get(
                "authors",
                []
            )

            if not title or not authors:
                continue

            author = authors[0].strip()

            published_raw = volume_info.get(
                "publishedDate",
                ""
            )

            publication_date = parse_publication_date(
                published_raw
            )

            actual_year = (
                publication_date.year
                if publication_date
                else year
            )

            # -------------------------------------------------
            # Keep only books matching requested year
            # when Google gives us an actual year.
            # -------------------------------------------------

            if publication_date:

                if publication_date.year != int(year):

                    continue

            image_links = volume_info.get(
                "imageLinks",
                {}
            )

            image = (
                image_links.get("thumbnail")
                or image_links.get("smallThumbnail")
                or ""
            )

            # Google sometimes gives http image URLs.
            if image.startswith("http://"):
                image = image.replace(
                    "http://",
                    "https://",
                    1,
                )

            info_link = volume_info.get(
                "infoLink",
                ""
            )

            books.append(
                {
                    "id": item.get("id", ""),
                    "title": title,
                    "author": author,
                    "year": actual_year,
                    "genre": genre,
                    "url": info_link,
                    "image": image,
                    "publisher": volume_info.get(
                        "publisher",
                        "",
                    ),
                    "description": volume_info.get(
                        "description",
                        "",
                    ),
                    "publication_date": publication_date,
                }
            )

        return books, None

    except requests.exceptions.Timeout:

        return [], "Google Books request timed out."

    except requests.exceptions.RequestException as e:

        return [], f"Google Books API error: {e}"

    except ValueError:

        return [], "Google Books returned invalid JSON."

    except Exception as e:

        return [], f"Unexpected error: {e}"


# =========================================================
# AMAZON SEARCH
# =========================================================

def amazon_search_url(title, author):

    query = quote(
        f"{title} {author}"
    )

    return (
        "https://www.amazon.com/s"
        f"?k={query}"
    )


# =========================================================
# SESSION STATE
# =========================================================

if "fetched_books" not in st.session_state:

    st.session_state.fetched_books = []


# =========================================================
# SIDEBAR
# =========================================================

db = DB()

with st.sidebar:

    st.markdown("## 📚 Indie Finder")

    st.divider()

    st.metric(
        "Books",
        db.count_books(),
    )

    st.metric(
        "Authors",
        db.count_authors(),
    )

    st.divider()

    if st.button(
        "🗑️ Clear All Data",
        use_container_width=True,
    ):

        db.clear()

        st.session_state.fetched_books = []

        st.success("Database cleared.")

        st.rerun()


# =========================================================
# HEADER
# =========================================================

st.title("📚 Indie Author Finder")

st.caption(
    "Discover books through Google Books and build a local author database."
)


# =========================================================
# FILTERS
# =========================================================

st.subheader("🔍 Search Filters")

c1, c2, c3, c4 = st.columns(4)

with c1:

    genre_f = st.selectbox(
        "Genre",
        GENRES,
    )

with c2:

    location_f = st.selectbox(
        "Location",
        USA_STATES,
    )

with c3:

    month_f = st.selectbox(
        "Publication Month",
        MONTHS,
    )

with c4:

    year_f = st.selectbox(
        "Publication Year",
        YEARS,
    )


st.divider()


# =========================================================
# FETCH
# =========================================================

if st.button(
    "📖 Fetch Books from Google",
    type="primary",
    use_container_width=True,
):

    year_val = (
        2026
        if year_f == "All Years"
        else int(year_f)
    )

    genre_val = (
        "Fiction"
        if genre_f == "All Genres"
        else genre_f
    )

    with st.spinner(
        "Searching Google Books..."
    ):

        books, error = fetch_books_from_api(
            genre=genre_val,
            year=year_val,
            max_results=20,
        )

    if error:

        st.error(error)

    elif books:

        st.session_state.fetched_books = books

        st.success(
            f"Found {len(books)} books."
        )

    else:

        st.session_state.fetched_books = []

        st.warning(
            "No matching books were found. "
            "Try another genre or year."
        )


# =========================================================
# FETCHED BOOKS
# =========================================================

if st.session_state.fetched_books:

    books = st.session_state.fetched_books

    st.subheader(
        f"🔎 Google Results ({len(books)})"
    )

    # -----------------------------------------------------
    # Add all
    # -----------------------------------------------------

    if st.button(
        f"➕ Add All {len(books)} Books",
        use_container_width=True,
    ):

        added = 0
        skipped = 0

        progress = st.progress(0)

        for index, bk in enumerate(books):

            success, message = db.add_book(
                title=bk["title"],
                author_name=bk["author"],
                genre=bk["genre"],
                year=bk["year"],
                url=bk["url"],
                image=bk["image"],
                publisher=bk["publisher"],
                description=bk["description"],
                google_book_id=bk["id"],
                publication_date=bk[
                    "publication_date"
                ],
            )

            if success:
                added += 1
            else:
                skipped += 1

            progress.progress(
                (index + 1) / len(books)
            )

        st.success(
            f"Added {added} books."
        )

        if skipped:
            st.info(
                f"{skipped} duplicate books were skipped."
            )

    st.divider()

    # -----------------------------------------------------
    # Individual books
    # -----------------------------------------------------

    for index, bk in enumerate(books):

        with st.container():

            col1, col2 = st.columns(
                [1, 5]
            )

            with col1:

                if bk.get("image"):

                    try:

                        st.image(
                            bk["image"],
                            width=100,
                        )

                    except Exception:

                        st.write("📖")

                else:

                    st.write("📖")

            with col2:

                st.markdown(
                    f"### {bk['title']}"
                )

                st.write(
                    f"**Author:** {bk['author']}"
                )

                st.write(
                    f"**Genre:** {bk['genre']}"
                )

                st.write(
                    f"**Publication Year:** {bk['year']}"
                )

                if bk.get("publisher"):

                    st.write(
                        f"**Publisher:** "
                        f"{bk['publisher']}"
                    )

                if bk.get("publication_date"):

                    st.write(
                        "**Publication Date:** "
                        f"{bk['publication_date'].strftime('%B %d, %Y')}"
                    )

                col_a, col_b, col_c = st.columns(3)

                with col_a:

                    if bk.get("url"):

                        st.link_button(
                            "Google Books",
                            bk["url"],
                        )

                with col_b:

                    st.link_button(
                        "Amazon Search",
                        amazon_search_url(
                            bk["title"],
                            bk["author"],
                        ),
                    )

                with col_c:

                    if st.button(
                        "➕ Add",
                        key=f"add_book_{index}_{bk['id']}",
                    ):

                        success, message = db.add_book(
                            title=bk["title"],
                            author_name=bk["author"],
                            genre=bk["genre"],
                            year=bk["year"],
                            url=bk["url"],
                            image=bk["image"],
                            publisher=bk["publisher"],
                            description=bk["description"],
                            google_book_id=bk["id"],
                            publication_date=bk[
                                "publication_date"
                            ],
                        )

                        if success:

                            st.success(
                                "Book added."
                            )

                        else:

                            st.warning(
                                message
                            )

            st.divider()


# =========================================================
# DATABASE RESULTS
# =========================================================

st.subheader("📚 Books in Database")

db = DB()

database_books = db.get_books(
    genre=genre_f,
    location=location_f,
    month=month_f,
    year=year_f,
    limit=100,
)

st.write(
    f"**Results: {len(database_books)} books**"
)


if not database_books:

    st.info(
        "No books match your current filters."
    )

else:

    for index, book in enumerate(
        database_books
    ):

        with st.container():

            col1, col2 = st.columns(
                [1, 5]
            )

            with col1:

                if book.cover_image:

                    try:

                        st.image(
                            book.cover_image,
                            width=100,
                        )

                    except Exception:

                        st.write("📖")

                else:

                    st.write("📖")

            with col2:

                st.markdown(
                    f"### {book.title}"
                )

                author_name = (
                    book.author.name
                    if book.author
                    else "Unknown"
                )

                author_state = (
                    book.author.state
                    if book.author
                    and book.author.state
                    else "Location unknown"
                )

                st.write(
                    f"**Author:** {author_name}"
                )

                st.write(
                    f"**Location:** {author_state}"
                )

                st.write(
                    f"**Genre:** {book.genre or 'Unknown'}"
                )

                if book.publication_date:

                    st.write(
                        "**Published:** "
                        f"{book.publication_date.strftime('%B %d, %Y')}"
                    )

                elif book.publication_year:

                    st.write(
                        f"**Published:** {book.publication_year}"
                    )

                if book.publisher:

                    st.write(
                        f"**Publisher:** {book.publisher}"
                    )

                st.write(
                    f"**Indie Score:** "
                    f"{book.indie_score}/100"
                )

                col_a, col_b = st.columns(2)

                with col_a:

                    if book.google_books_url:

                        st.link_button(
                            "Google Books",
                            book.google_books_url,
                        )

                with col_b:

                    st.link_button(
                        "Amazon Search",
                        amazon_search_url(
                            book.title,
                            author_name,
                        ),
                    )

            st.divider()


# =========================================================
# FOOTER
# =========================================================

st.caption(
    "Indie Author Finder v15.0"
)
