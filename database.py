"""Database operations"""
from sqlalchemy import create_engine, and_, func, distinct
from sqlalchemy.orm import sessionmaker, joinedload
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import config
from models import Base, Author, Book, DailyDiscoveryLog

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DATABASE_PATH
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

    def add_author(self, name: str, **kwargs) -> Author:
        session = self.get_session()
        try:
            author = session.query(Author).filter(func.lower(Author.name) == func.lower(name)).first()
            if not author:
                author = Author(name=name, **kwargs)
                session.add(author)
                session.commit()
            return author
        finally:
            session.close()

    def count_authors(self) -> int:
        session = self.get_session()
        try:
            return session.query(func.count(Author.id)).scalar()
        finally:
            session.close()

    def add_book(self, title: str, author_id: int, publication_date: date, **kwargs) -> Optional[Book]:
        session = self.get_session()
        try:
            pub_year = publication_date.year
            existing = session.query(Book).filter(and_(func.lower(Book.title) == func.lower(title), Book.author_id == author_id, Book.publication_year == pub_year)).first()
            if existing:
                return None
            book = Book(title=title, author_id=author_id, publication_date=publication_date, publication_month=publication_date.strftime('%B'), publication_year=pub_year, date_found=date.today(), first_seen=date.today(), last_checked=date.today(), **kwargs)
            session.add(book)
            session.commit()
            return book
        finally:
            session.close()

    def get_books(self, filters: Dict = None, limit: int = 100) -> List[Book]:
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

    def count_books(self) -> int:
        session = self.get_session()
        try:
            return session.query(func.count(Book.id)).scalar()
        finally:
            session.close()

    def get_new_today(self) -> int:
        session = self.get_session()
        try:
            return session.query(func.count(Book.id)).filter(Book.date_found == date.today()).scalar()
        finally:
            session.close()

    def get_new_this_month(self) -> int:
        session = self.get_session()
        try:
            return session.query(func.count(Book.id)).filter(Book.date_found >= date.today().replace(day=1)).scalar()
        finally:
            session.close()

    def log_discovery(self, books_found: int, new_authors: int, duplicates: int, failed: int) -> DailyDiscoveryLog:
        session = self.get_session()
        try:
            log = DailyDiscoveryLog(discovery_date=date.today(), books_found=books_found, new_authors_found=new_authors, duplicates_removed=duplicates, failed_sources=failed, last_run_time=datetime.utcnow(), status='completed')
            session.add(log)
            session.commit()
            return log
        finally:
            session.close()

    def get_discovery_history(self, limit: int = 30) -> List[DailyDiscoveryLog]:
        session = self.get_session()
        try:
            return session.query(DailyDiscoveryLog).order_by(DailyDiscoveryLog.discovery_date.desc()).limit(limit).all()
        finally:
            session.close()

    def export_books(self, filters: Dict = None) -> List[Dict]:
        books = self.get_books(filters, limit=10000)
        return [{'title': b.title, 'author_name': b.author.name, 'genre': b.genre, 'publication_date': b.publication_date.isoformat(), 'indie_score': b.indie_score, 'amazon_url': b.amazon_url} for b in books]
