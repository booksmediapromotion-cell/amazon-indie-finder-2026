import streamlit as st
import requests
import time
import pandas as pd

from datetime import date
from urllib.parse import quote

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Date,
    ForeignKey,
    or_,
    inspect,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Indie Author Finder 2026",
    page_icon="📚",
    layout="wide",
)


# ============================================================
# CONSTANTS
# ============================================================

USA_STATES = [
    "All Locations",
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
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

YEARS = [
    "All Years",
    2026,
    2025,
    2024,
    2023,
    2022,
    2021,
    2020,
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

LEAD_STATUSES = [
    "New",
    "Qualified",
    "Contacted",
    "Response",
    "Not Interested",
]

PUBLISHER_MAJOR_KEYWORDS = [
    "penguin",
    "random house",
    "harpercollins",
    "simon & schuster",
    "simon and schuster",
    "hachette",
    "macmillan",
    "scholastic",
    "simon",
    "wiley",
    "oxford university press",
    "cambridge university press",
    "bloomsbury",
    "knopf",
    "doubleday",
    "santa monica press",
]

PUBLISHER_INDEPENDENT_KEYWORDS = [
    "independent",
    "indie",
    "self",
    "author",
    "publishing",
    "press",
    "books",
    "publishing house",
    "llc",
]


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = "sqlite:///indie_authors.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# ============================================================
# MODELS
# ============================================================

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)

    state = Column(String(100), default="")
    country = Column(String(100), default="")

    website = Column(String(500), default="")
    email = Column(String(255), default="")

    linkedin_url = Column(String(500), default="")
    instagram_url = Column(String(500), default="")
    tiktok_url = Column(String(500), default="")

    amazon_author_url = Column(String(500), default="")

    openlibrary_author_id = Column(String(100), default="")
    openlibrary_author_url = Column(String(500), default="")

    author_source_url = Column(String(500), default="")

    location = Column(String(255), default="")

    indie_likelihood = Column(Integer, default=50)
    lead_score = Column(Integer, default=0)

    lead_status = Column(String(50), default="New")

    notes = Column(Text, default="")

    created_at = Column(Date, default=date.today)

    books = relationship(
        "Book",
        back_populates="author",
        cascade="all, delete-orphan",
    )


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)

    google_book_id = Column(String(255), unique=True, nullable=True)

    openlibrary_work_id = Column(String(255), default="")

    isbn = Column(String(100), default="")

    title = Column(String(500), nullable=False)

    author_id = Column(
        Integer,
        ForeignKey("authors.id"),
        nullable=False,
    )

    genre = Column(String(100), default="")

    publication_date = Column(Date, nullable=True)

    publication_month = Column(Integer, nullable=True)
    publication_year = Column(Integer, nullable=True)

    google_books_url = Column(String(1000), default="")
    openlibrary_url = Column(String(1000), default="")
    amazon_url = Column(String(1000), default="")

    cover_image = Column(String(1000), default="")

    publisher = Column(String(500), default="")

    description = Column(Text, default="")

    source_url = Column(String(1000), default="")

    date_found = Column(Date, default=date.today)

    indie_score = Column(Integer, default=50)

    author = relationship(
        "Author",
        back_populates="books",
    )


# ============================================================
# DATABASE SETUP
# ============================================================

Base.metadata.create_all(engine)


def get_existing_columns(table_name):
    inspector = inspect(engine)

    try:
        return {
            column["name"]
            for column in inspector.get_columns(table_name)
        }
    except Exception:
        return set()


def add_missing_columns(table_name, columns):
    existing = get_existing_columns(table_name)

    if not existing:
        return

    with engine.begin() as connection:

        for column_name, column_type in columns.items():

            if column_name not in existing:

                try:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )
                except Exception:
                    pass


def migrate_database():

    author_columns = {
        "state": "VARCHAR(100)",
        "country": "VARCHAR(100)",
        "website": "VARCHAR(500)",
        "email": "VARCHAR(255)",
        "linkedin_url": "VARCHAR(500)",
        "instagram_url": "VARCHAR(500)",
        "tiktok_url": "VARCHAR(500)",
        "amazon_author_url": "VARCHAR(500)",
        "openlibrary_author_id": "VARCHAR(100)",
        "openlibrary_author_url": "VARCHAR(500)",
        "author_source_url": "VARCHAR(500)",
        "location": "VARCHAR(255)",
        "indie_likelihood": "INTEGER",
        "lead_score": "INTEGER",
        "lead_status": "VARCHAR(50)",
        "notes": "TEXT",
        "created_at": "DATE",
    }

    book_columns = {
        "google_book_id": "VARCHAR(255)",
        "openlibrary_work_id": "VARCHAR(255)",
        "isbn": "VARCHAR(100)",
        "genre": "VARCHAR(100)",
        "publication_date": "DATE",
        "publication_month": "INTEGER",
        "publication_year": "INTEGER",
        "google_books_url": "VARCHAR(1000)",
        "openlibrary_url": "VARCHAR(1000)",
        "amazon_url": "VARCHAR(1000)",
        "cover_image": "VARCHAR(1000)",
        "publisher": "VARCHAR(500)",
        "description": "TEXT",
        "source_url": "VARCHAR(1000)",
        "date_found": "DATE",
        "indie_score": "INTEGER",
    }

    add_missing_columns(
        "authors",
        author_columns,
    )

    add_missing_columns(
        "books",
        book_columns,
    )


migrate_database()


# ============================================================
# DATABASE HELPERS
# ============================================================

def calculate_indie_likelihood(publisher):

    if not publisher:
        return 50

    publisher_lower = publisher.lower().strip()

    for keyword in PUBLISHER_MAJOR_KEYWORDS:

        if keyword in publisher_lower:
            return 20

    for keyword in PUBLISHER_INDEPENDENT_KEYWORDS:

        if keyword in publisher_lower:
            return 65

    return 50


def calculate_lead_score(
    author,
    book_count=0,
):

    score = 0

    if book_count >= 3:
        score += 20

    elif book_count >= 2:
        score += 15

    elif book_count >= 1:
        score += 10

    if author.indie_likelihood >= 65:
        score += 25

    elif author.indie_likelihood >= 50:
        score += 15

    if author.website:
        score += 10

    if author.email:
        score += 15

    if author.linkedin_url:
        score += 5

    if author.instagram_url:
        score += 5

    if author.tiktok_url:
        score += 5

    if author.amazon_author_url:
        score += 5

    return min(score, 100)


def amazon_search_url(title, author):

    query = f"{title} {author}"

    return (
        "https://www.amazon.com/s?"
        "k=" + quote(query)
    )


def parse_date(value):

    if not value:
        return None

    try:

        value = str(value)

        if len(value) == 4:
            return date(
                int(value),
                1,
                1,
            )

        if len(value) == 7:
            year, month = value.split("-")

            return date(
                int(year),
                int(month),
                1,
            )

        return date.fromisoformat(
            value[:10]
        )

    except Exception:
        return None


def month_name(month_number):

    if not month_number:
        return ""

    try:
        return date(
            2000,
            month_number,
            1,
        ).strftime("%B")

    except Exception:
        return ""


# ============================================================
# AUTHOR HELPERS
# ============================================================

def get_or_create_author(
    session,
    name,
    openlibrary_author_id="",
):

    name = (
        name.strip()
        if name
        else "Unknown Author"
    )

    author = (
        session.query(Author)
        .filter(
            Author.name.ilike(name)
        )
        .first()
    )

    if author:
        if (
            openlibrary_author_id
            and not author.openlibrary_author_id
        ):
            author.openlibrary_author_id = (
                openlibrary_author_id
            )

            author.openlibrary_author_url = (
                "https://openlibrary.org/authors/"
                + openlibrary_author_id
            )

            session.commit()

        return author

    author = Author(
        name=name,
        openlibrary_author_id=openlibrary_author_id or "",
        openlibrary_author_url=(
            "https://openlibrary.org/authors/"
            + openlibrary_author_id
            if openlibrary_author_id
            else ""
        ),
        lead_status="New",
        created_at=date.today(),
    )

    session.add(author)

    session.commit()

    return author


def update_author_score(session, author):

    book_count = (
        session.query(Book)
        .filter(
            Book.author_id == author.id
        )
        .count()
    )

    author.lead_score = calculate_lead_score(
        author,
        book_count,
    )

    session.commit()


def add_book(book_data):

    session = SessionLocal()

    try:

        title = book_data.get(
            "title",
            "",
        ).strip()

        author_name = book_data.get(
            "author",
            "Unknown Author",
        ).strip()

        if not title:
            return False, "Missing title."

        google_id = book_data.get(
            "google_book_id"
        )

        openlibrary_id = book_data.get(
            "openlibrary_work_id"
        )

        existing = None

        if google_id:

            existing = (
                session.query(Book)
                .filter(
                    Book.google_book_id
                    == google_id
                )
                .first()
            )

        if not existing:

            existing = (
                session.query(Book)
                .join(Author)
                .filter(
                    Book.title.ilike(title),
                    Author.name.ilike(
                        author_name
                    ),
                )
                .first()
            )

        if existing:

            return False, "Already saved."

        author = get_or_create_author(
            session,
            author_name,
            book_data.get(
                "openlibrary_author_id",
                "",
            ),
        )

        publisher = book_data.get(
            "publisher",
            "",
        )

        publication_date = parse_date(
            book_data.get(
                "publishedDate"
            )
        )

        indie_score = (
            calculate_indie_likelihood(
                publisher
            )
        )

        book = Book(
            google_book_id=google_id,
            openlibrary_work_id=(
                openlibrary_id or ""
            ),
            isbn=book_data.get(
                "isbn",
                "",
            ),
            title=title,
            author_id=author.id,
            genre=book_data.get(
                "genre",
                "",
            ),
            publication_date=publication_date,
            publication_month=(
                publication_date.month
                if publication_date
                else None
            ),
            publication_year=(
                publication_date.year
                if publication_date
                else None
            ),
            google_books_url=book_data.get(
                "google_books_url",
                "",
            ),
            openlibrary_url=book_data.get(
                "openlibrary_url",
                "",
            ),
            amazon_url=amazon_search_url(
                title,
                author_name,
            ),
            cover_image=book_data.get(
                "cover_image",
                "",
            ),
            publisher=publisher,
            description=book_data.get(
                "description",
                "",
            ),
            source_url=book_data.get(
                "source_url",
                "",
            ),
            date_found=date.today(),
            indie_score=indie_score,
        )

        session.add(book)

        session.commit()

        update_author_score(
            session,
            author,
        )

        return True, "Saved."

    except Exception as e:

        session.rollback()

        return False, str(e)

    finally:

        session.close()


# ============================================================
# GOOGLE BOOKS
# ============================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def google_books_search(
    genre,
    year,
    limit=30,
):

    if genre == "All Genres":
        genre_query = "books"

    else:
        genre_query = genre

    query = f"{genre_query} books"

    if year != "All Years":
        query += f" {year}"

    url = (
        "https://www.googleapis.com/books/v1/volumes"
    )

    params = {
        "q": query,
        "maxResults": min(
            int(limit),
            40,
        ),
        "orderBy": "newest",
        "printType": "books",
    }

    headers = {
        "User-Agent":
            "IndieAuthorFinder/1.0"
    }

    for attempt in range(3):

        try:

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=20,
            )

            if response.status_code == 429:

                time.sleep(
                    2 ** attempt
                )

                continue

            response.raise_for_status()

            data = response.json()

            results = []

            for item in data.get(
                "items",
                [],
            ):

                info = item.get(
                    "volumeInfo",
                    {},
                )

                title = info.get(
                    "title",
                    "",
                )

                authors = info.get(
                    "authors",
                    [],
                )

                author_name = (
                    authors[0]
                    if authors
                    else "Unknown Author"
                )

                published = info.get(
                    "publishedDate",
                    "",
                )

                parsed_date = parse_date(
                    published
                )

                if (
                    year != "All Years"
                    and parsed_date
                    and parsed_date.year
                    != int(year)
                ):
                    continue

                image = info.get(
                    "imageLinks",
                    {},
                ).get(
                    "thumbnail",
                    "",
                )

                if image.startswith(
                    "http://"
                ):
                    image = image.replace(
                        "http://",
                        "https://",
                        1,
                    )

                results.append({

                    "google_book_id":
                        item.get("id"),

                    "openlibrary_work_id":
                        "",

                    "openlibrary_author_id":
                        "",

                    "isbn":
                        (
                            info.get(
                                "industryIdentifiers",
                                [{}],
                            )[0].get(
                                "identifier",
                                "",
                            )
                            if info.get(
                                "industryIdentifiers"
                            )
                            else ""
                        ),

                    "title":
                        title,

                    "author":
                        author_name,

                    "genre":
                        genre
                        if genre != "All Genres"
                        else "",

                    "publishedDate":
                        published,

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

                    "cover_image":
                        image,

                    "google_books_url":
                        info.get(
                            "infoLink",
                            "",
                        ),

                    "openlibrary_url":
                        "",

                    "source_url":
                        info.get(
                            "infoLink",
                            "",
                        ),

                })

            return results, "Google Books"

        except Exception:
            time.sleep(
                2 ** attempt
            )

    return [], "Google Books unavailable"


# ============================================================
# OPEN LIBRARY
# ============================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def open_library_search(
    genre,
    year,
    limit=50,
):

    url = (
        "https://openlibrary.org/search.json"
    )

    if genre == "All Genres":
        query = "*"

    else:
        query = genre

    if year != "All Years":
        query += f" first_publish_year:{year}"

    params = {
        "q": query,
        "limit": min(
            int(limit),
            100,
        ),
        "sort": "new",
        "fields": (
            "key,title,author_name,"
            "author_key,first_publish_year,"
            "cover_i,publisher,isbn"
        ),
    }

    headers = {
        "User-Agent":
            "IndieAuthorFinder/1.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=25,
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for doc in data.get(
            "docs",
            [],
        ):

            publish_year = doc.get(
                "first_publish_year"
            )

            if (
                year != "All Years"
                and publish_year
                and int(publish_year)
                != int(year)
            ):
                continue

            title = doc.get(
                "title",
                "",
            )

            authors = doc.get(
                "author_name",
                [],
            )

            author_keys = doc.get(
                "author_key",
                [],
            )

            author_name = (
                authors[0]
                if authors
                else "Unknown Author"
            )

            author_key = (
                author_keys[0]
                if author_keys
                else ""
            )

            work_key = doc.get(
                "key",
                "",
            )

            if work_key.startswith(
                "/works/"
            ):
                work_id = work_key.split(
                    "/"
                )[-1]
            else:
                work_id = work_key

            cover_id = doc.get(
                "cover_i"
            )

            cover_url = ""

            if cover_id:

                cover_url = (
                    "https://covers.openlibrary.org/"
                    f"b/id/{cover_id}-L.jpg"
                )

            publishers = doc.get(
                "publisher",
                [],
            )

            publisher = (
                publishers[0]
                if publishers
                else ""
            )

            isbns = doc.get(
                "isbn",
                [],
            )

            isbn = (
                isbns[0]
                if isbns
                else ""
            )

            results.append({

                "google_book_id":
                    None,

                "openlibrary_work_id":
                    work_id,

                "openlibrary_author_id":
                    author_key,

                "isbn":
                    isbn,

                "title":
                    title,

                "author":
                    author_name,

                "genre":
                    genre
                    if genre != "All Genres"
                    else "",

                "publishedDate":
                    str(publish_year)
                    if publish_year
                    else "",

                "publisher":
                    publisher,

                "description":
                    "",

                "cover_image":
                    cover_url,

                "google_books_url":
                    "",

                "openlibrary_url":
                    (
                        "https://openlibrary.org"
                        + work_key
                        if work_key
                        else ""
                    ),

                "source_url":
                    (
                        "https://openlibrary.org"
                        + work_key
                        if work_key
                        else ""
                    ),
            })

        return results, "Open Library"

    except Exception:

        return [], "Open Library unavailable"


# ============================================================
# FETCH
# ============================================================

def fetch_books(
    genre,
    year,
    limit,
):

    google_results, google_status = (
        google_books_search(
            genre,
            year,
            limit,
        )
    )

    if google_results:

        return google_results, google_status

    open_results, open_status = (
        open_library_search(
            genre,
            year,
            limit,
        )
    )

    return open_results, open_status


# ============================================================
# AUTHOR SEARCH LINKS
# ============================================================

def google_search_url(
    author_name,
    extra="",
):

    query = (
        f'"{author_name}" {extra}'
        if extra
        else f'"{author_name}"'
    )

    return (
        "https://www.google.com/search?q="
        + quote(query)
    )


def author_search_links(author_name):

    return {

        "Website":
            google_search_url(
                author_name
            ),

        "LinkedIn":
            google_search_url(
                author_name,
                "author LinkedIn",
            ),

        "Instagram":
            google_search_url(
                author_name,
                "author Instagram",
            ),

        "TikTok":
            google_search_url(
                author_name,
                "author TikTok",
            ),

        "Email":
            google_search_url(
                author_name,
                "author email contact",
            ),
    }


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📚 Indie Author Finder")

st.sidebar.caption(
    "Find and organize potential indie-author leads."
)

session = SessionLocal()

try:

    total_books = session.query(Book).count()

    total_authors = session.query(
        Author
    ).count()

    qualified = session.query(
        Author
    ).filter(
        Author.lead_status == "Qualified"
    ).count()

    contacted = session.query(
        Author
    ).filter(
        Author.lead_status == "Contacted"
    ).count()

finally:

    session.close()


st.sidebar.metric(
    "Authors",
    total_authors,
)

st.sidebar.metric(
    "Books",
    total_books,
)

st.sidebar.metric(
    "Qualified Leads",
    qualified,
)

st.sidebar.metric(
    "Contacted",
    contacted,
)


st.sidebar.divider()


if st.sidebar.button(
    "🗑 Clear Database",
    use_container_width=True,
):

    session = SessionLocal()

    try:

        session.query(Book).delete()

        session.query(Author).delete()

        session.commit()

        st.cache_data.clear()

        st.sidebar.success(
            "Database cleared."
        )

        st.rerun()

    except Exception as e:

        session.rollback()

        st.sidebar.error(
            str(e)
        )

    finally:

        session.close()


# ============================================================
# HEADER
# ============================================================

st.title(
    "📚 Indie Author Finder 2026"
)

st.write(
    "Discover books, build author profiles, "
    "qualify potential marketing leads, and "
    "export your author database."
)

st.divider()


# ============================================================
# TABS
# ============================================================

tab_discover, tab_authors, tab_books = st.tabs(
    [
        "🔎 Discover",
        "👤 Authors",
        "📚 Saved Books",
    ]
)


# ============================================================
# DISCOVER TAB
# ============================================================

with tab_discover:

    st.subheader(
        "Find New Books & Authors"
    )

    col1, col2, col3, col4 = st.columns(
        4
    )

    with col1:

        genre = st.selectbox(
            "Genre",
            GENRES,
        )

    with col2:

        year = st.selectbox(
            "Publication Year",
            YEARS,
        )

    with col3:

        result_limit = st.selectbox(
            "Results",
            [10, 20, 30, 40, 50],
            index=1,
        )

    with col4:

        st.write("")

        search_button = st.button(
            "🔎 Find Books",
            type="primary",
            use_container_width=True,
        )


    if search_button:

        with st.spinner(
            "Searching book databases..."
        ):

            results, source_name = (
                fetch_books(
                    genre,
                    year,
                    result_limit,
                )
            )

        st.session_state[
            "fetched_books"
        ] = results

        st.session_state[
            "source_name"
        ] = source_name


    results = st.session_state.get(
        "fetched_books",
        [],
    )

    source_name = st.session_state.get(
        "source_name",
        "",
    )


    if source_name:

        st.info(
            f"Source: **{source_name}**"
        )


    if results:

        st.success(
            f"Found {len(results)} books."
        )

        if st.button(
            "➕ Add All Results",
            type="primary",
        ):

            added = 0
            skipped = 0

            for book in results:

                success, message = add_book(
                    book
                )

                if success:
                    added += 1

                else:
                    skipped += 1

            st.success(
                f"Added {added} books."
            )

            if skipped:
                st.info(
                    f"{skipped} duplicates or invalid records skipped."
                )

            st.rerun()


        st.divider()


        for index, book in enumerate(
            results
        ):

            with st.container(
                border=True
            ):

                col_img, col_info, col_actions = st.columns(
                    [1, 5, 2]
                )

                with col_img:

                    image = book.get(
                        "cover_image",
                        "",
                    )

                    if image:

                        st.image(
                            image,
                            width=100,
                        )

                with col_info:

                    st.markdown(
                        f"### {book.get('title', 'Untitled')}"
                    )

                    st.write(
                        f"**Author:** "
                        f"{book.get('author', 'Unknown')}"
                    )

                    st.write(
                        f"**Publisher:** "
                        f"{book.get('publisher') or 'Unknown'}"
                    )

                    st.write(
                        f"**Published:** "
                        f"{book.get('publishedDate') or 'Unknown'}"
                    )

                    publisher = book.get(
                        "publisher",
                        "",
                    )

                    indie_score = (
                        calculate_indie_likelihood(
                            publisher
                        )
                    )

                    st.write(
                        f"**Indie likelihood:** "
                        f"{indie_score}/100"
                    )

                    if (
                        indie_score >= 65
                    ):

                        st.success(
                            "Potential independent/self-published signal"
                        )

                    elif (
                        indie_score <= 20
                    ):

                        st.warning(
                            "Publisher appears to be a major publisher"
                        )

                    else:

                        st.caption(
                            "Indie status unclear — verify before outreach."
                        )

                with col_actions:

                    if st.button(
                        "➕ Add",
                        key=f"add_{index}",
                        use_container_width=True,
                    ):

                        success, message = (
                            add_book(book)
                        )

                        if success:

                            st.success(
                                "Saved."
                            )

                        else:

                            st.warning(
                                message
                            )

                    if book.get(
                        "google_books_url"
                    ):

                        st.link_button(
                            "Google Books",
                            book[
                                "google_books_url"
                            ],
                            use_container_width=True,
                        )

                    if book.get(
                        "openlibrary_url"
                    ):

                        st.link_button(
                            "Open Library",
                            book[
                                "openlibrary_url"
                            ],
                            use_container_width=True,
                        )

                    st.link_button(
                        "Amazon Search",
                        amazon_search_url(
                            book.get(
                                "title",
                                "",
                            ),
                            book.get(
                                "author",
                                "",
                            ),
                        ),
                        use_container_width=True,
                    )


# ============================================================
# AUTHORS TAB
# ============================================================

with tab_authors:

    st.subheader(
        "👤 Author Leads"
    )

    session = SessionLocal()

    try:

        authors = (
            session.query(Author)
            .order_by(
                Author.lead_score.desc(),
                Author.name.asc(),
            )
            .all()
        )

        if not authors:

            st.info(
                "No authors saved yet. "
                "Go to Discover and add books."
            )

        else:

            col1, col2, col3, col4 = st.columns(
                4
            )

            with col1:

                status_filter = st.selectbox(
                    "Lead Status",
                    [
                        "All Statuses"
                    ] + LEAD_STATUSES,
                )

            with col2:

                location_filter = st.selectbox(
                    "Location",
                    [
                        "All Locations"
                    ] + sorted(
                        {
                            a.location
                            for a in authors
                            if a.location
                        }
                    ),
                )

            with col3:

                min_score = st.slider(
                    "Minimum Lead Score",
                    0,
                    100,
                    0,
                )

            with col4:

                search_author = st.text_input(
                    "Search Author",
                    placeholder="Author name...",
                )


            filtered_authors = []

            for author in authors:

                if (
                    status_filter
                    != "All Statuses"
                    and author.lead_status
                    != status_filter
                ):
                    continue

                if (
                    location_filter
                    != "All Locations"
                    and author.location
                    != location_filter
                ):
                    continue

                if (
                    author.lead_score
                    < min_score
                ):
                    continue

                if (
                    search_author
                    and search_author.lower()
                    not in author.name.lower()
                ):
                    continue

                filtered_authors.append(
                    author
                )


            st.write(
                f"Showing **{len(filtered_authors)}** authors."
            )


            if filtered_authors:

                export_rows = []

                for author in filtered_authors:

                    book_count = (
                        session.query(Book)
                        .filter(
                            Book.author_id
                            == author.id
                        )
                        .count()
                    )

                    export_rows.append({

                        "Author":
                            author.name,

                        "Location":
                            author.location,

                        "State":
                            author.state,

                        "Country":
                            author.country,

                        "Email":
                            author.email,

                        "Website":
                            author.website,

                        "LinkedIn":
                            author.linkedin_url,

                        "Instagram":
                            author.instagram_url,

                        "TikTok":
                            author.tiktok_url,

                        "Amazon Author":
                            author.amazon_author_url,

                        "Open Library Author":
                            author.openlibrary_author_url,

                        "Books":
                            book_count,

                        "Indie Likelihood":
                            author.indie_likelihood,

                        "Lead Score":
                            author.lead_score,

                        "Status":
                            author.lead_status,

                        "Notes":
                            author.notes,

                    })


                export_df = pd.DataFrame(
                    export_rows
                )

                csv_data = (
                    export_df
                    .to_csv(
                        index=False
                    )
                    .encode("utf-8")
                )

                st.download_button(
                    "📥 Export Authors CSV",
                    data=csv_data,
                    file_name=(
                        "indie_author_leads.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                )


                st.divider()


                for author in filtered_authors:

                    book_count = (
                        session.query(Book)
                        .filter(
                            Book.author_id
                            == author.id
                        )
                        .count()
                    )

                    with st.expander(
                        f"⭐ {author.name} "
                        f"— Lead Score {author.lead_score}/100"
                    ):

                        left, right = st.columns(
                            [2, 1]
                        )

                        with left:

                            st.markdown(
                                f"### {author.name}"
                            )

                            st.write(
                                f"**Books saved:** "
                                f"{book_count}"
                            )

                            st.write(
                                f"**Indie likelihood:** "
                                f"{author.indie_likelihood}/100"
                            )

                            st.write(
                                f"**Location:** "
                                f"{author.location or 'Not provided'}"
                            )

                            st.write(
                                f"**Email:** "
                                f"{author.email or 'Not provided'}"
                            )

                            st.write(
                                f"**Website:** "
                                f"{author.website or 'Not provided'}"
                            )

                            st.write(
                                f"**LinkedIn:** "
                                f"{author.linkedin_url or 'Not provided'}"
                            )

                            st.write(
                                f"**Instagram:** "
                                f"{author.instagram_url or 'Not provided'}"
                            )

                            st.write(
                                f"**TikTok:** "
                                f"{author.tiktok_url or 'Not provided'}"
                            )

                            st.write(
                                f"**Amazon Author:** "
                                f"{author.amazon_author_url or 'Not provided'}"
                            )


                            if author.openlibrary_author_url:

                                st.link_button(
                                    "Open Library Author",
                                    author.openlibrary_author_url,
                                )


                        with right:

                            current_status = st.selectbox(
                                "Lead Status",
                                LEAD_STATUSES,
                                index=(
                                    LEAD_STATUSES.index(
                                        author.lead_status
                                    )
                                    if author.lead_status
                                    in LEAD_STATUSES
                                    else 0
                                ),
                                key=(
                                    f"status_{author.id}"
                                ),
                            )


                            if st.button(
                                "💾 Save Status",
                                key=(
                                    f"save_status_{author.id}"
                                ),
                                use_container_width=True,
                            ):

                                author.lead_status = (
                                    current_status
                                )

                                session.commit()

                                st.success(
                                    "Status updated."
                                )

                                st.rerun()


                            st.markdown(
                                "**Find Public Profiles**"
                            )

                            links = (
                                author_search_links(
                                    author.name
                                )
                            )

                            st.link_button(
                                "🌐 Search Website",
                                links["Website"],
                                use_container_width=True,
                            )

                            st.link_button(
                                "LinkedIn Search",
                                links["LinkedIn"],
                                use_container_width=True,
                            )

                            st.link_button(
                                "Instagram Search",
                                links["Instagram"],
                                use_container_width=True,
                            )

                            st.link_button(
                                "TikTok Search",
                                links["TikTok"],
                                use_container_width=True,
                            )

                            st.link_button(
                                "Public Contact Search",
                                links["Email"],
                                use_container_width=True,
                            )


                        st.divider()


                        edit1, edit2 = st.columns(
                            2
                        )

                        with edit1:

                            website = st.text_input(
                                "Website",
                                value=author.website or "",
                                key=(
                                    f"website_{author.id}"
                                ),
                            )

                            email = st.text_input(
                                "Public/business email",
                                value=author.email or "",
                                key=(
                                    f"email_{author.id}"
                                ),
                            )

                            location = st.text_input(
                                "Location",
                                value=author.location or "",
                                key=(
                                    f"location_{author.id}"
                                ),
                            )

                            state = st.text_input(
                                "State",
                                value=author.state or "",
                                key=(
                                    f"state_{author.id}"
                                ),
                            )

                            country = st.text_input(
                                "Country",
                                value=author.country or "",
                                key=(
                                    f"country_{author.id}"
                                ),
                            )

                        with edit2:

                            linkedin = st.text_input(
                                "LinkedIn URL",
                                value=(
                                    author.linkedin_url
                                    or ""
                                ),
                                key=(
                                    f"linkedin_{author.id}"
                                ),
                            )

                            instagram = st.text_input(
                                "Instagram URL",
                                value=(
                                    author.instagram_url
                                    or ""
                                ),
                                key=(
                                    f"instagram_{author.id}"
                                ),
                            )

                            tiktok = st.text_input(
                                "TikTok URL",
                                value=(
                                    author.tiktok_url
                                    or ""
                                ),
                                key=(
                                    f"tiktok_{author.id}"
                                ),
                            )

                            amazon_author = st.text_input(
                                "Amazon Author URL",
                                value=(
                                    author.amazon_author_url
                                    or ""
                                ),
                                key=(
                                    f"amazon_author_{author.id}"
                                ),
                            )

                            notes = st.text_area(
                                "Notes",
                                value=author.notes or "",
                                key=(
                                    f"notes_{author.id}"
                                ),
                            )


                        if st.button(
                            "💾 Save Author Information",
                            key=(
                                f"save_author_{author.id}"
                            ),
                            type="primary",
                        ):

                            author.website = website.strip()

                            author.email = email.strip()

                            author.location = (
                                location.strip()
                            )

                            author.state = state.strip()

                            author.country = (
                                country.strip()
                            )

                            author.linkedin_url = (
                                linkedin.strip()
                            )

                            author.instagram_url = (
                                instagram.strip()
                            )

                            author.tiktok_url = (
                                tiktok.strip()
                            )

                            author.amazon_author_url = (
                                amazon_author.strip()
                            )

                            author.notes = notes.strip()

                            author.lead_score = (
                                calculate_lead_score(
                                    author,
                                    book_count,
                                )
                            )

                            session.commit()

                            st.success(
                                "Author updated."
                            )

                            st.rerun()


    except Exception as e:

        st.error(
            f"Could not load authors: {e}"
        )

    finally:

        session.close()


# ============================================================
# BOOKS TAB
# ============================================================

with tab_books:

    st.subheader(
        "📚 Saved Books"
    )

    session = SessionLocal()

    try:

        genre_filter = st.selectbox(
            "Genre",
            GENRES,
            key="saved_genre",
        )

        location_filter = st.selectbox(
            "Author Location",
            [
                "All Locations"
            ]
            + USA_STATES[1:],
            key="saved_location",
        )

        month_filter = st.selectbox(
            "Publication Month",
            MONTHS,
            key="saved_month",
        )

        year_filter = st.selectbox(
            "Publication Year",
            YEARS,
            key="saved_year",
        )


        query = (
            session.query(Book)
            .join(Author)
        )


        if (
            genre_filter
            != "All Genres"
        ):

            query = query.filter(
                Book.genre
                == genre_filter
            )


        if (
            location_filter
            != "All Locations"
        ):

            if location_filter == "Other":

                query = query.filter(
                    or_(
                        Author.state == "",
                        Author.state.is_(None),
                    )
                )

            else:

                query = query.filter(
                    Author.state
                    == location_filter
                )


        if (
            month_filter
            != "All Months"
        ):

            month_number = (
                list(
                    MONTHS
                ).index(
                    month_filter
                )
            )

            query = query.filter(
                Book.publication_month
                == month_number
            )


        if (
            year_filter
            != "All Years"
        ):

            query = query.filter(
                Book.publication_year
                == int(year_filter)
            )


        books = (
            query
            .order_by(
                Book.publication_date.desc()
            )
            .limit(500)
            .all()
        )


        st.write(
            f"Showing **{len(books)}** saved books."
        )


        if books:

            rows = []

            for book in books:

                rows.append({

                    "Title":
                        book.title,

                    "Author":
                        book.author.name
                        if book.author
                        else "",

                    "Publisher":
                        book.publisher,

                    "Genre":
                        book.genre,

                    "Publication Date":
                        (
                            book.publication_date
                            if book.publication_date
                            else ""
                        ),

                    "Indie Score":
                        book.indie_score,

                    "Lead Score":
                        (
                            book.author.lead_score
                            if book.author
                            else 0
                        ),

                    "Lead Status":
                        (
                            book.author.lead_status
                            if book.author
                            else ""
                        ),

                    "ISBN":
                        book.isbn,

                    "Amazon":
                        book.amazon_url,

                })


            df = pd.DataFrame(rows)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )


            csv = (
                df
                .to_csv(
                    index=False
                )
                .encode("utf-8")
            )

            st.download_button(
                "📥 Export Books CSV",
                data=csv,
                file_name=(
                    "saved_books.csv"
                ),
                mime="text/csv",
            )


        else:

            st.info(
                "No saved books match these filters."
            )


    except Exception as e:

        st.error(
            f"Could not load books: {e}"
        )

    finally:

        session.close()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Indie Author Finder v17.0 • "
    "Google Books + Open Library • "
    "Lead management"
)

st.caption(
    "Indie likelihood is an evidence-based signal, "
    "not proof of self-publishing. Verify author "
    "information before outreach."
)
