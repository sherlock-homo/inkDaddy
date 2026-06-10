from __future__ import annotations

from collections.abc import Generator

from .config import get_settings

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
except ModuleNotFoundError as exc:  # pragma: no cover - exercised before deps are installed
    raise RuntimeError(
        "SQLAlchemy is required for the hub database. Install backend dependencies with "
        '`pip install -e ".[dev]"`.'
    ) from exc


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    from . import models  # noqa: F401

    settings.ensure_data_dirs()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
