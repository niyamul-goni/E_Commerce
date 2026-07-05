from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import Base

# Supabase (and most managed Postgres providers) require SSL.
# connect_args is passed through to psycopg2 and is silently
# ignored for local connections, so this works in both environments.
_connect_args: dict = {}
if settings.DATABASE_URL and ("supabase.co" in settings.DATABASE_URL or "supabase.com" in settings.DATABASE_URL):
    _connect_args = {"sslmode": "require"}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

