"""
Database Engine & Session Management for GeM TenderLens.
Provides PostgreSQL connection initialization via SQLAlchemy with automatic fallback handling.
"""

import os
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from utils_logger import get_logger

load_dotenv()

logger = get_logger(__name__)

# Primary database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/tenderlens_fallback.db"
)
FALLBACK_SQLITE_URL = "sqlite:///./data/tenderlens_fallback.db"

Base = declarative_base()

_engine = None
_SessionLocal = None


def _ensure_postgres_db_exists(url: str):
    """Attempts to create the target PostgreSQL database if it does not exist."""
    try:
        from urllib.parse import urlparse
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        parsed = urlparse(url)
        db_name = parsed.path.lstrip("/")
        if not db_name or db_name == "postgres":
            return

        # Connect to default 'postgres' database
        user = parsed.username or "postgres"
        password = parsed.password or ""
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432

        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port,
            connect_timeout=5
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cur.fetchone():
            logger.info(f"Database '{db_name}' does not exist on PostgreSQL server. Creating it now...")
            # Enclose identifier in double quotes safely
            cur.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"Database '{db_name}' created successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not auto-create PostgreSQL database '{url}': {e}")


def get_engine():
    """Returns or creates the active SQLAlchemy engine."""
    global _engine, _SessionLocal
    if _engine is not None:
        return _engine

    target_url = DATABASE_URL
    try:
        if target_url.startswith("postgresql"):
            _ensure_postgres_db_exists(target_url)
            engine = create_engine(target_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
            # Test connection
            with engine.connect() as conn:
                logger.info(f"Connected successfully to PostgreSQL database at: {target_url.split('@')[-1]}")
            _engine = engine
        else:
            connect_args = {"check_same_thread": False} if target_url.startswith("sqlite") else {}
            _engine = create_engine(target_url, connect_args=connect_args)
    except Exception as e:
        logger.warning(
            f"Failed to connect to primary database '{target_url}': {e}. "
            f"Falling back to local SQLite database: {FALLBACK_SQLITE_URL}"
        )
        os.makedirs("./data", exist_ok=True)
        _engine = create_engine(FALLBACK_SQLITE_URL, connect_args={"check_same_thread": False})

    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session_factory():
    """Returns sessionmaker bound to active engine."""
    global _SessionLocal
    if _SessionLocal is None:
        get_engine()
    return _SessionLocal


def init_db():
    """Creates database tables if they do not exist."""
    try:
        engine = get_engine()
        # Import models so Base metadata is populated
        import services.db_models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
        return True
    except Exception as e:
        logger.error(f"Error during database table initialization: {e}")
        return False


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for managing transactional database sessions."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session rolled back due to error: {e}")
        raise
    finally:
        session.close()
