"""
Database session management for the Shathyar Translation backend.

Provides a SQLAlchemy Session dependency for FastAPI routes with
SQLite persistence by default. The database URL can be overridden
via the SHATHYAR_DB_URL environment variable.
"""

import os
from contextlib import contextmanager
from typing import Generator
from urllib.parse import parse_qsl, urlparse, urlencode, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models.translation_entry import Base  # ensures Base is defined
# Import models to register them with SQLAlchemy metadata before create_all
from .models import official_dictionary as _od  # noqa: F401
from .models import user_session as _us  # noqa: F401
from sqlalchemy import text
from .utils.normalize import normalize_text


def _column_exists(conn, table: str, column: str) -> bool:
    try:
        res = conn.execute(text(f"PRAGMA table_info({table})"))
        return any(row[1] == column for row in res.fetchall())
    except Exception:
        return False


def _safe_add_column(conn, table: str, column_def: str) -> None:
    try:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_def}"))
    except Exception:
        # If column exists or ALTER not allowed, ignore
        pass


def _backfill_normalized_columns(conn) -> None:
    """Backfill normalized columns for existing rows (SQLite only)."""
    try:
        # Official dictionary
        if _column_exists(conn, 'official_dictionary', 'origin_cn'):
            if not _column_exists(conn, 'official_dictionary', 'norm_origin_cn'):
                _safe_add_column(conn, 'official_dictionary', 'norm_origin_cn TEXT')
            if not _column_exists(conn, 'official_dictionary', 'norm_shathyar'):
                _safe_add_column(conn, 'official_dictionary', 'norm_shathyar TEXT')
            rows = conn.execute(text('SELECT id, origin_cn, shathyar FROM official_dictionary')).fetchall()
            for r in rows:
                norm_cn = normalize_text(r[1] or '')
                norm_sh = normalize_text(r[2] or '')
                conn.execute(text('UPDATE official_dictionary SET norm_origin_cn=:ncn, norm_shathyar=:nsh WHERE id=:id'),
                             dict(ncn=norm_cn, nsh=norm_sh, id=r[0]))
        # Translation entries
        if _column_exists(conn, 'translation_entries', 'source_text'):
            if not _column_exists(conn, 'translation_entries', 'norm_source_text'):
                _safe_add_column(conn, 'translation_entries', 'norm_source_text TEXT')
            if not _column_exists(conn, 'translation_entries', 'norm_translated_text'):
                _safe_add_column(conn, 'translation_entries', 'norm_translated_text TEXT')
            rows = conn.execute(text('SELECT id, source_text, translated_text FROM translation_entries')).fetchall()
            for r in rows:
                norm_src = normalize_text(r[1] or '')
                norm_tr = normalize_text(r[2] or '')
                conn.execute(text('UPDATE translation_entries SET norm_source_text=:ns, norm_translated_text=:nt WHERE id=:id'),
                             dict(ns=norm_src, nt=norm_tr, id=r[0]))
        conn.commit()
    except Exception:
        pass


def _normalize_db_url(url: str) -> str:
    """Normalize and sanitize DB URL for SQLAlchemy/DBAPI compatibility.

    - Convert "postgres://" to "postgresql://".
    - For PostgreSQL URLs, drop unsupported query params (e.g., directConnection).
    - Map common provider flags (e.g., ssl=true -> sslmode=require).
    """
    try:
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]

        if url.startswith("postgresql://") or url.startswith("postgresql+"):
            parsed = urlparse(url)
            # Parse query string and normalize known flags
            q = dict(parse_qsl(parsed.query, keep_blank_values=True))

            # Some providers set non-psycopg2 flags; remap or drop
            if "ssl" in q and "sslmode" not in q:
                v = (q.pop("ssl") or "").lower()
                if v in {"1", "true", "yes", "on", "require"}:
                    q["sslmode"] = "require"
                elif v in {"0", "false", "no", "off"}:
                    q["sslmode"] = "disable"

            # Allowlist of psycopg2 connection options
            allowed = {
                "sslmode",
                "application_name",
                "connect_timeout",
                "options",
                "client_encoding",
                "keepalives",
                "keepalives_idle",
                "keepalives_interval",
                "keepalives_count",
                "target_session_attrs",
                "service",
                # TLS file-based options (occasionally provided)
                "sslrootcert",
                "sslcert",
                "sslkey",
                "sslpassword",
                "sslcrl",
                # Newer libpq options
                "gssencmode",
                "ssl_min_protocol_version",
                "ssl_max_protocol_version",
            }

            filtered = {k: v for k, v in q.items() if k in allowed}

            # Rebuild URL with filtered query
            url = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    urlencode(filtered, doseq=True),
                    parsed.fragment,
                )
            )
    except Exception:
        # If anything goes wrong, fall back to original URL
        return url

    return url


def _default_db_url() -> str:
    # Prefer explicit env var
    env = os.getenv('SHATHYAR_DB_URL') or os.getenv('DATABASE_URL')
    if env:
        return env
    # Use repo root absolute path to keep DB consistent regardless of CWD
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    db_path = (root / 'shathyar.db').as_posix()
    return f"sqlite:///{db_path}"


DB_URL = _normalize_db_url(_default_db_url())

# For SQLite, disable same-thread check to allow use in async context wrappers
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Create tables if they do not exist yet (idempotent)
Base.metadata.create_all(bind=engine)

def _migrate_legacy(conn) -> None:
    """Migrate data from legacy SQLite DB (e.g., backend/shathyar.db) if present.

    Only migrates when current DB is empty to avoid duplication.
    """
    try:
        from pathlib import Path
        # If we already have translation entries, skip migration
        has_table = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='translation_entries'")).scalar() or 0
        if has_table:
            cur_count = conn.execute(text('SELECT COUNT(*) FROM translation_entries')).scalar() or 0
            if cur_count:
                return

        # Find legacy DB
        root = Path(__file__).resolve().parents[2]
        candidates = [root / 'backend' / 'shathyar.db', root / 'shathyar.db']
        legacy_path = next((p for p in candidates if p.exists()), None)
        if not legacy_path:
            return

        # Attach and copy
        conn.execute(text("ATTACH DATABASE :path AS legacy"), {"path": str(legacy_path)})

        def table_exists(schema: str, name: str) -> bool:
            q = text("SELECT COUNT(*) FROM " + schema + ".sqlite_master WHERE type='table' AND name=:n")
            return (conn.execute(q, {"n": name}).scalar() or 0) > 0

        if table_exists('legacy', 'official_dictionary'):
            conn.execute(text("""
                INSERT INTO official_dictionary (id, origin_cn, shathyar, origin_en, created_at, checksum)
                SELECT id, origin_cn, shathyar, origin_en, created_at, checksum FROM legacy.official_dictionary
            """))
        if table_exists('legacy', 'translation_entries'):
            conn.execute(text("""
                INSERT INTO translation_entries (
                    id, source_text, translated_text, source_language, is_ai_generated,
                    is_user_confirmed, confidence_score, created_at, updated_at, usage_count
                )
                SELECT id, source_text, translated_text, source_language, is_ai_generated,
                       is_user_confirmed, confidence_score, created_at, updated_at, usage_count
                FROM legacy.translation_entries
            """))
        if table_exists('legacy', 'user_sessions'):
            try:
                conn.execute(text('INSERT INTO user_sessions SELECT * FROM legacy.user_sessions'))
            except Exception:
                pass

        conn.execute(text('DETACH DATABASE legacy'))
        conn.commit()
    except Exception:
        # Migration is best-effort
        pass

# Run migration then backfill for normalized columns
with engine.begin() as conn:
    _migrate_legacy(conn)
    _backfill_normalized_columns(conn)


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and ensures cleanup."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
