"""PostgreSQL connection, engine, and session management."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.models.base import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _connect_args(settings: Settings) -> dict[str, int]:
    return {"connect_timeout": settings.database_connect_timeout_seconds}


def get_engine(settings: Settings | None = None) -> Engine:
    """Return or create the SQLAlchemy engine singleton."""
    global _engine
    if _engine is None:
        settings = settings or get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.database_echo,
            connect_args=_connect_args(settings),
        )
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    """Return or create the session factory singleton."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(settings),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope(settings: Settings | None = None) -> Generator[Session, None, None]:
    """Context manager for scripts and tests — commits or rolls back."""
    factory = get_session_factory(settings)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_connection(settings: Settings | None = None) -> bool:
    """Return True if PostgreSQL accepts a connection and responds to SELECT 1."""
    settings = settings or get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def dispose_engine() -> None:
    """Dispose engine on application shutdown."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None


def get_metadata():
    """Expose SQLAlchemy metadata for Alembic autogenerate."""
    return Base.metadata
