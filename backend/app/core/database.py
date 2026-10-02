"""Database engine and session setup - the one place SQLAlchemy is configured."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# The engine manages the actual pool of connections to Postgres.
engine = create_engine(settings.database_url)

# A factory that creates new DB sessions (one per request) bound to the engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class every ORM model (User, Task, etc.) will inherit from."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency - gives a route one DB session, closes it when the request ends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
