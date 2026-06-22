"""PostgreSQL connection, engine, and session management."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.core.tenant.context import get_effective_tenant_id
from app.models.base import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None
_session_events_configured = False


def set_rls_tenant_context(db: Session, tenant_id: uuid.UUID | None) -> None:
    """
    Bind PostgreSQL RLS session variable for the current transaction.

    Uses set_config(..., is_local=true) equivalent to SET LOCAL app.tenant_id.
    Production connections should use the non-superuser `hms_app` database role
    so FORCE ROW LEVEL SECURITY policies apply.
    """
    if tenant_id is None:
        db.execute(text("RESET app.tenant_id"))
        return
    db.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


def use_rls_enforced_role(db: Session) -> None:
    """Switch to hms_app role so RLS applies (superusers bypass RLS)."""
    db.execute(text("SET ROLE hms_app"))


def configure_session_events() -> None:
    """Register SQLAlchemy session hooks for tenant RLS (idempotent)."""
    global _session_events_configured
    if _session_events_configured:
        return

    @event.listens_for(Session, "after_begin")
    def _apply_rls_on_transaction_begin(session, transaction, connection) -> None:  # noqa: ARG001
        tenant_id = get_effective_tenant_id()
        if tenant_id is not None:
            connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )

    _session_events_configured = True


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
        configure_session_events()
        _SessionLocal = sessionmaker(
            bind=get_engine(settings),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session with tenant RLS when bound."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        tenant_id = get_effective_tenant_id()
        if tenant_id is not None:
            set_rls_tenant_context(db, tenant_id)
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
