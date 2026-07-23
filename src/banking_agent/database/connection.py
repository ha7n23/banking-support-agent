from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from banking_agent.core.config import DATABASE_URL


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_database_url() -> str:
    """Return the configured database URL or fail with a clear message."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL must be set when using PostgreSQL workflow storage."
        )

    return DATABASE_URL


def get_engine() -> Engine:
    """Return a lazily-created SQLAlchemy engine."""
    global _engine

    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            pool_pre_ping=True,
        )

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return a lazily-created SQLAlchemy session factory."""
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
        )

    return _session_factory


def get_database_session() -> Generator[Session, None, None]:
    """Yield a database session and close it after use."""
    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield session
    finally:
        session.close()