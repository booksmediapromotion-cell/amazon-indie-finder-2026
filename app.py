"""
Indie Author Finder v16
Google Books + Open Library
Streamlit + SQLite + SQLAlchemy
"""

import streamlit as st
from datetime import date, datetime
from urllib.parse import quote
import requests
import time

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
    text,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
    joinedload,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Indie Author Finder",
    page_icon="📚",
    layout="wide",
)


# =========================================================
# OPTIONS
# =========================================================

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
    "Other",
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
# DATABASE MODELS
# =========================================================

Base = declarative_base()


class Author(Base):

    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)

    name = Column(
        String(255),
        nullable=False,
    )

    state = Column(
        String(100),
        default="",
    )

    country = Column(
        String(100),
        default="USA",
    )

    website = Column(
        String(500),
        default="",
    )

    email = Column(
        String(255),
        default="",
    )

    amazon_author_url = Column(
        String(500),
        default="",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


class Book(Base):

    __tablename__ = "books"

    id = Column(
        Integer,
        primary_key=True,
    )

    google_book_id = Column(
        String(255),
        unique=True,
        nullable=True,
    )

    title = Column(
        String(500),
        nullable=False,
    )

    author_id = Column(
        Integer,
        ForeignKey("authors.id"),
        nullable=False,
    )

    genre = Column(
        String(100),
        default="",
    )

    publication_date = Column(
        Date,
        nullable=True,
    )

    publication_month = Column(
        String(20),
        default="",
    )

    publication_year = Column(
        Integer,
        nullable=True,
    )

    google_books_url = Column(
        String(500),
        default="",
    )

    amazon_url = Column(
        String(500),
        default="",
    )

    cover_image = Column(
        String(500),
        default="",
    )

    publisher = Column(
        String(255),
        default="",
    )

    description = Column(
        Text,
        default="",
    )

    source_url = Column(
        String(500),
        default="",
    )

    date_found = Column(
        Date,
        default=date.today,
    )

    indie_score = Column(
        Integer,
        default=50,
    )

    author = relationship(
        "Author",
        backref="books",
    )


# =========================================================
# DATABASE
# =========================================================

class DB:

    def __init__(self):

        self.engine = create_engine(
            "sqlite:///indie_authors.db",
            connect_args={
                "check_same_thread": False
            },
        )

        Base.metadata.create_all(
            self.engine
        )

        self.Session = sessionmaker(
            bind=self.engine
        )

        self.migrate_database()

    def session(self):

        return self.Session()

    # -----------------------------------------------------
    # Automatic SQLite migration
    # -----------------------------------------------------

    def migrate_database(self):

        with self.engine.begin() as conn:

            # AUTHORS
            author_columns = {
                "website": "VARCHAR(500)",
                "email": "VARCHAR(255)",
                "amazon_author_url": "VARCHAR(500)",
            }

            self.add_missing_columns(
                conn,
                "authors",
                author_columns,
            )

            # BOOKS
            book_columns = {
                "google_book_id": "VARCHAR(255)",
                "publication_date": "DATE",
                "publication_month": "VARCHAR(20)",
                "publication_year": "INTEGER",
                "google_books_url": "VARCHAR(500)",
                "amazon_url": "VARCHAR(500)",
                "cover_image": "VARCHAR(500)",
                "publisher": "VARCHAR(255)",
                "description": "TEXT",
                "source_url": "VARCHAR(500)",
                "date_found": "DATE",
                "indie_score": "INTEGER",
            }

            self.add_missing_columns(
                conn,
                "books",
                book_columns,
            )

    def add_missing_columns(
        self,
        conn,
        table_name,
        columns,
    ):

        result = conn.execute(
            text(
                f"PRAGMA table_info({table_name})"
            )
        )

        existing = {
            row[1]
            for row in result.fetchall()
        }

        for column_name, column_type in columns.items():

            if column_name not in existing:

                try:

                    conn.execute(
                        text(
                            f"ALTER TABLE "
                            f"{table_name} "
                            f"ADD COLUMN "
                            f"{column_name} "
                            f"{column_type}"
                        )
                    )

                except Exception:
                    pass

    # -----------------------------------------------------
    # Counts
    # -----------------------------------------------------

    def count_books(self):

        s = self.session()

        try:

            return (
                s.query(
                    func.count(Book.id)
                ).scalar()
                or 0
            )

        finally:

            s.close()

    def count_authors(self):

        s = self.session()

        try:

            return (
                s.query(
                    func.count(Author.id)
                ).scalar()
                or 0
            )

        finally:

            s.close()

    # -----------------------------------------------------
    # Clear
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Check duplicate
    # -----------------------------------------------------

    def book_exists(
        self,
        google_book_id=None,
        title=None,
        author_name=None,
    ):

        s = self.session()

        try:

            if google_book_id:

                found = (
                    s.query(Book)
                    .filter(
                        Book.google_book_id
                        == google_book_id
                    )
                    .first()
                )

                if found:
                    return True

            if title and author_name:

                found = (
                    s.query(Book)
                    .join(Author)
                    .filter(
                        func.lower(
                            Book.title
                        )
                        == func.lower(title),

                        func.lower(
                            Author.name
                        )
                        == func.lower(
                            author_name
                        ),
                    )
                    .first()
                )

                if found:
                    return True

            return False

        finally:

            s.close()

    # -----------------------------------------------------
    # Add book
    # -----------------------------------------------------

    def add_book(
        self,
        title,
        author_name,
        genre="",
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

            # Google ID duplicate
            if google_book_id:

                existing = (
                    s.query(Book)
                    .filter(
                        Book.google_book_id
                        == google_book_id
                    )
                    .first()
                )

                if existing:

                    return (
                        False,
                        "Book already exists."
                    )

            # Find author
            author = (
                s.query(Author)
                .filter(
                    func.lower(
                        Author.name
                    )
                    == func.lower(
                        author_name
                    )
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

            # Title + author duplicate
            existing = (
                s.query(Book)
                .filter(
                    func.lower(
                        Book.title
                    )
                    == func.lower(title),

                    Book.author_id
                    == author.id,
                )
                .first()
            )

            if existing:

                return (
                    False,
                    "Book already exists."
                )

            # Publication date
            pub_date = publication_date

            if pub_date is None and year:

                try:

                    pub_date = date(
                        int(year),
                        1,
                        1,
                    )

                except Exception:

                    pub_date = None

            pub_month = ""

            if pub_date:

                pub_month = (
                    pub_date.strftime("%B")
                )

            score = calculate_indie_score(
                publisher
            )

            book = Book(
                google_book_id=google_book_id,
                title=title,
                author_id=author.id,
                genre=genre,
                publication_date=pub_date,
                publication_month=pub_month,
                publication_year=(
                    pub_date.year
                    if pub_date
                    else year
                ),
                google_books_url=url,
                amazon_url=amazon_search_url(
                    title,
                    author_name,
                ),
                cover_image=image,
                publisher=publisher,
                description=description,
                source_url=url,
                date_found=date.today(),
                indie_score=score,
            )

            s.add(book)

            s.commit()

            return (
                True,
                "Book added."
            )

        except Exception as e:

            s.rollback()

            return (
                False,
                str(e)
            )

        finally:

            s.close()

    # -----------------------------------------------------
    # Get books
    # -----------------------------------------------------

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
                .options(
                    joinedload(
                        Book.author
                    )
                )
            )

            if genre != "All Genres":

                q = q.filter(
                    Book.genre == genre
                )

            if location != "All Locations":

                q = (
                    q.join(
                        Book.author
                    )
                    .filter(
                        Author.state
                        == location
                    )
                )

            if month != "All Months":

                q = q.filter(
                    Book.publication_month
                    == month
                )

            if year != "All Years":

                q = q.filter(
                    Book.publication_year
                    == int(year)
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

def calculate_indie_score(
    publisher=""
):

    if not publisher:

        return 50

    publisher = publisher.lower()

    major_publishers = [
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

    for name in major_publishers:

        if name in publisher:

            return 20

    independent_terms = [
        "independent",
        "indie",
        "self",
        "author",
        "publishing",
        "press",
        "books",
    ]

    for term in independent_terms:

        if term in publisher:

            return 65

    return 50


# =========================================================
# DATE PARSER
# =========================================================

def parse_date(value):

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

            return datetime.strptime(
                value,
                fmt,
            ).date()

        except ValueError:

            continue

    return None


# =========================================================
# AMAZON SEARCH
# =========================================================

def amazon_search_url(
    title,
    author,
):

    query = quote(
        f"{title} {author}"
    )

    return (
        "https://www.amazon.com/s"
        f"?k={query}"
    )


# =========================================================
# GOOGLE BOOKS
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def google_books_search(
    genre,
    year,
    max_results=20,
):

    url = (
        "https://www.googleapis.com/"
        "books/v1/volumes"
    )

    query = (
        f"{genre} books {year}"
    )

    params = {
        "q": query,
        "maxResults": min(
            max_results,
            40,
        ),
        "orderBy": "newest",
        "printType": "books",
    }

    headers = {
        "User-Agent":
            "Mozilla/5.0 "
            "(compatible; "
            "IndieAuthorFinder/16.0)"
    }

    for attempt in range(3):

        try:

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=20,
            )

            # Rate limited
            if response.status_code == 429:

                if attempt < 2:

                    time.sleep(
                        2 ** attempt
                    )

                    continue

                return (
                    [],
                    "Google Books is temporarily rate-limiting requests."
                )

            response.raise_for_status()

            data = response.json()

            books = []

            for item in data.get(
                "items",
                [],
            ):

                info = item.get(
                    "volumeInfo",
                    {},
                )

                title = (
                    info.get(
                        "title",
                        ""
                    )
                    .strip()
                )

                authors = info.get(
                    "authors",
                    [],
                )

                if not title or not authors:

                    continue

                author = (
                    authors[0]
                    .strip()
                )

                raw_date = info.get(
                    "publishedDate",
                    "",
                )

                pub_date = parse_date(
                    raw_date
                )

                actual_year = (
                    pub_date.year
                    if pub_date
                    else year
                )

                # If Google gives actual
                # year, make sure it matches
                if pub_date:

                    if (
                        pub_date.year
                        != int(year)
                    ):

                        continue

                images = info.get(
                    "imageLinks",
                    {},
                )

                image = (
                    images.get(
                        "thumbnail"
                    )
                    or images.get(
                        "smallThumbnail"
                    )
                    or ""
                )

                if image.startswith(
                    "http://"
                ):

                    image = image.replace(
                        "http://",
                        "https://",
                        1,
                    )

                books.append(
                    {
                        "id":
                            item.get(
                                "id",
                                "",
                            ),

                        "title":
                            title,

                        "author":
                            author,

                        "year":
                            actual_year,

                        "genre":
                            genre,

                        "url":
                            info.get(
                                "infoLink",
                                "",
                            ),

                        "image":
                            image,

                        "publisher":
                            info.get(
                                "publisher",
                                "",
                            ),

                        "description":
                            info.get(
                                "description",
                                "",
                            ),

                        "publication_date":
                            pub_date,
                    }
                )

            return books, None

        except requests.exceptions.Timeout:

            if attempt < 2:

                time.sleep(
                    2 ** attempt
                )

                continue

            return (
                [],
                "Google Books request timed out."
            )

        except requests.exceptions.RequestException as e:

            return (
                [],
                f"Google Books error: {e}"
            )

        except Exception as e:

            return (
                [],
                f"Google Books error: {e}"
            )

    return [], "Google Books unavailable."


# =========================================================
# OPEN LIBRARY
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def open_library_search(
    genre,
    year,
    max_results=20,
):

    url = (
        "https://openlibrary.org/"
        "search.json"
    )

    params = {
        "q": f"{genre} {year}",
        "limit": min(
            max_results,
            100,
        ),
        "sort": "new",
    }

    headers = {
        "User-Agent":
            "IndieAuthorFinder/16.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        books = []

        for item in data.get(
            "docs",
            [],
        ):

            title = (
                item.get(
                    "title",
                    ""
                )
                or ""
            ).strip()

            authors = item.get(
                "author_name",
                [],
            )

            if not title or not authors:

                continue

            author = (
                authors[0]
                .strip()
            )

            first_publish_year = (
                item.get(
                    "first_publish_year"
                )
            )

            if (
                first_publish_year
                and int(first_publish_year)
                != int(year)
            ):

                continue

            # Cover
            cover_id = item.get(
                "cover_i"
            )

            image = ""

            if cover_id:

                image = (
                    "https://covers.openlibrary.org/"
                    f"b/id/{cover_id}-M.jpg"
                )

            # ISBN
            isbns = item.get(
                "isbn",
                []
            )

            isbn = (
                isbns[0]
                if isbns
                else ""
            )

            books.append(
                {
                    "id":
                        f"openlibrary_{isbn or quote(title)}",

                    "title":
                        title,

                    "author":
                        author,

                    "year":
                        first_publish_year
                        or year,

                    "genre":
                        genre,

                    "url":
                        (
                            "https://openlibrary.org"
                            + item.get(
                                "key",
                                "",
                            )
                        ),

                    "image":
                        image,

                    "publisher":
                        (
                            item.get(
                                "publisher",
                                [""],
                            )
                            or [""]
                        )[0],

                    "description":
                        "",

                    "publication_date":
                        (
                            date(
                                int(
                                    first_publish_year
                                ),
                                1,
                                1,
                            )
                            if first_publish_year
                            else None
                        ),
                }
            )

        return books, None

    except requests.exceptions.Timeout:

        return (
            [],
            "Open Library request timed out."
        )

    except requests.exceptions.RequestException as e:

        return (
            [],
            f"Open Library error: {e}"
        )

    except Exception as e:

        return (
            [],
            f"Open Library error: {e}"
        )


# =========================================================
# COMBINED SEARCH
# =========================================================

def fetch_books(
    genre,
    year,
    max_results=20,
):

    # ---------------------------------------------
    # Try Google first
    # ---------------------------------------------

    google_books, google_error = (
        google_books_search(
            genre,
            year,
            max_results,
        )
    )

    if google_books:

        return (
            google_books,
            "Google Books",
            None,
        )

    # ---------------------------------------------
    # Google failed / 429
    # Try Open Library
    # ---------------------------------------------

    open_books, open_error = (
        open_library_search(
            genre,
            year,
            max_results,
        )
    )

    if open_books:

        return (
            open_books,
            "Open Library",
            google_error,
        )

    return (
        [],
        None,
        (
            google_error
            or open_error
            or "No books found."
        ),
    )


# =========================================================
# SESSION STATE
# =========================================================

if (
    "fetched_books"
    not in st.session_state
):

    st.session_state.fetched_books = []

if (
    "source_name"
    not in st.session_state
):

    st.session_state.source_name = ""


# =========================================================
# DATABASE
# =========================================================

db = DB()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        "## 📚 Indie Finder"
    )

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

    st.markdown(
        "**Data Sources**"
    )

    st.write(
        "✓ Google Books"
    )

    st.write(
        "✓ Open Library fallback"
    )

    st.divider()

    if st.button(
        "🗑️ Clear Database",
        use_container_width=True,
    ):

        db.clear()

        st.session_state.fetched_books = []

        st.success(
            "Database cleared."
        )

        st.rerun()


# =========================================================
# HEADER
# =========================================================

st.title(
    "📚 Indie Author Finder"
)

st.caption(
    "Discover books and build a local author database."
)


# =========================================================
# FILTERS
# =========================================================

st.subheader(
    "🔍 Search Filters"
)

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
# FETCH BUTTON
# =========================================================

if st.button(
    "📖 Find Books",
    type="primary",
    use_container_width=True,
):

    search_year = (
        2026
        if year_f == "All Years"
        else int(year_f)
    )

    search_genre = (
        "Fiction"
        if genre_f == "All Genres"
        else genre_f
    )

    with st.spinner(
        "Searching book databases..."
    ):

        books, source, error = fetch_books(
            search_genre,
            search_year,
            20,
        )

    if books:

        st.session_state.fetched_books = books

        st.session_state.source_name = (
            source
        )

        st.success(
            f"Found {len(books)} books "
            f"using {source}."
        )

        if error:

            st.info(
                "Google Books was unavailable, "
                "so Open Library was used instead."
            )

    else:

        st.session_state.fetched_books = []

        st.error(
            error
            or "No books were found."
        )


# =========================================================
# SEARCH RESULTS
# =========================================================

books = st.session_state.fetched_books

if books:

    st.subheader(
        f"🔎 Search Results — "
        f"{st.session_state.source_name}"
    )

    # -----------------------------------------------------
    # Add All
    # -----------------------------------------------------

    if st.button(
        f"➕ Add All {len(books)} Books",
        use_container_width=True,
    ):

        added = 0
        skipped = 0

        progress = st.progress(0)

        for i, book in enumerate(
            books
        ):

            success, message = (
                db.add_book(
                    title=book["title"],
                    author_name=book["author"],
                    genre=book["genre"],
                    year=book["year"],
                    url=book["url"],
                    image=book["image"],
                    publisher=book["publisher"],
                    description=book["description"],
                    google_book_id=book["id"],
                    publication_date=book[
                        "publication_date"
                    ],
                )
            )

            if success:

                added += 1

            else:

                skipped += 1

            progress.progress(
                (i + 1) / len(books)
            )

        st.success(
            f"Added {added} books."
        )

        if skipped:

            st.info(
                f"Skipped {skipped} "
                f"duplicate books."
            )

        time.sleep(0.5)

        st.rerun()

    st.divider()

    # -----------------------------------------------------
    # Individual results
    # -----------------------------------------------------

    for i, book in enumerate(
        books
    ):

        with st.container():

            col1, col2 = st.columns(
                [1, 5]
            )

            with col1:

                if book.get("image"):

                    try:

                        st.image(
                            book["image"],
                            width=100,
                        )

                    except Exception:

                        st.write("📖")

                else:

                    st.write("📖")

            with col2:

                st.markdown(
                    f"### {book['title']}"
                )

                st.write(
                    f"**Author:** "
                    f"{book['author']}"
                )

                st.write(
                    f"**Genre:** "
                    f"{book['genre']}"
                )

                st.write(
                    f"**Year:** "
                    f"{book['year']}"
                )

                if book.get(
                    "publisher"
                ):

                    st.write(
                        f"**Publisher:** "
                        f"{book['publisher']}"
                    )

                if book.get(
                    "publication_date"
                ):

                    st.write(
                        "**Published:** "
                        f"{book['publication_date'].strftime('%B %d, %Y')}"
                    )

                a, b, c = st.columns(
                    3
                )

                with a:

                    if book.get(
                        "url"
                    ):

                        st.link_button(
                            "📖 Book Page",
                            book["url"],
                        )

                with b:

                    st.link_button(
                        "🛒 Amazon",
                        amazon_search_url(
                            book["title"],
                            book["author"],
                        ),
                    )

                with c:

                    if st.button(
                        "➕ Add",
                        key=(
                            f"add_"
                            f"{i}_"
                            f"{book['id']}"
                        ),
                    ):

                        success, message = (
                            db.add_book(
                                title=book[
                                    "title"
                                ],
                                author_name=book[
                                    "author"
                                ],
                                genre=book[
                                    "genre"
                                ],
                                year=book[
                                    "year"
                                ],
                                url=book[
                                    "url"
                                ],
                                image=book[
                                    "image"
                                ],
                                publisher=book[
                                    "publisher"
                                ],
                                description=book[
                                    "description"
                                ],
                                google_book_id=book[
                                    "id"
                                ],
                                publication_date=book[
                                    "publication_date"
                                ],
                            )
                        )

                        if success:

                            st.success(
                                "Added!"
                            )

                            time.sleep(
                                0.3
                            )

                            st.rerun()

                        else:

                            st.warning(
                                message
                            )

            st.divider()


# =========================================================
# DATABASE
# =========================================================

st.subheader(
    "📚 Books in Database"
)

try:

    database_books = (
        db.get_books(
            genre=genre_f,
            location=location_f,
            month=month_f,
            year=year_f,
            limit=100,
        )
    )

    st.write(
        f"**Results: "
        f"{len(database_books)} books**"
    )

    if not database_books:

        st.info(
            "No books match your "
            "current filters."
        )

    else:

        for book in database_books:

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

                    if book.author:

                        author_name = (
                            book.author.name
                        )

                        author_state = (
                            book.author.state
                            or
                            "Location unknown"
                        )

                    else:

                        author_name = (
                            "Unknown"
                        )

                        author_state = (
                            "Location unknown"
                        )

                    st.write(
                        f"**Author:** "
                        f"{author_name}"
                    )

                    st.write(
                        f"**Location:** "
                        f"{author_state}"
                    )

                    if book.genre:

                        st.write(
                            f"**Genre:** "
                            f"{book.genre}"
                        )

                    if (
                        book.publication_date
                    ):

                        st.write(
                            "**Published:** "
                            f"{book.publication_date.strftime('%B %d, %Y')}"
                        )

                    elif (
                        book.publication_year
                    ):

                        st.write(
                            "**Published:** "
                            f"{book.publication_year}"
                        )

                    if book.publisher:

                        st.write(
                            f"**Publisher:** "
                            f"{book.publisher}"
                        )

                    st.write(
                        f"**Indie Score:** "
                        f"{book.indie_score}/100"
                    )

                    a, b = st.columns(2)

                    with a:

                        if (
                            book.google_books_url
                        ):

                            st.link_button(
                                "📖 Book Page",
                                book.google_books_url,
                            )

                    with b:

                        st.link_button(
                            "🛒 Amazon",
                            amazon_search_url(
                                book.title,
                                author_name,
                            ),
                        )

                st.divider()

except Exception as e:

    st.error(
        "The database could not be loaded."
    )

    st.code(
        str(e)
    )

    st.info(
        "The app was prevented from crashing. "
        "Check your database schema or "
        "redeploy the application."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Indie Author Finder v16.0 • "
    "Google Books + Open Library"
)
