from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings


def _create_engine() -> Engine:
    kwargs: dict[str, object] = {"echo": settings.sql_echo, "future": True}
    if settings.is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 15}

    engine = create_engine(settings.database_url, **kwargs)
    if not settings.is_sqlite:
        return engine

    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]
        # The pysqlite driver must not open implicit transactions: every unit of
        # work explicitly takes the write lock below.
        dbapi_connection.isolation_level = None
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()

    @event.listens_for(engine, "begin")
    def _begin_immediate(conn) -> None:  # type: ignore[no-untyped-def]
        # Serialising writers is what makes the forced-close invariant hold when
        # two suppliers bid at the same millisecond.
        conn.exec_driver_sql("BEGIN IMMEDIATE")

    return engine


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
