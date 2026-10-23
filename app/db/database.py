"""
ScamShield AI — Database & Repository Layer (Items 1, 9, 10, 18)

Provides a lightweight, zero-dependency SQLite repository layer
with WAL mode, foreign key enforcement, and strict user data isolation.
"""

import os
from pathlib import Path
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional

from app.config import settings


def get_db_path() -> Path:
    """
    Returns the active database path.
    Enforces strict test isolation: in test mode, connecting to the live database
    or running without an isolated database path raises RuntimeError.
    """
    target = settings.DB_PATH
    is_testing = (
        os.getenv("SCAMSHIELD_TEST_MODE") == "1"
        or "PYTEST_CURRENT_TEST" in os.environ
        or "pytest" in sys.modules
    )
    if is_testing:
        live_db = (settings.BASE_DIR / "data" / "scamshield.db").resolve()
        if target.resolve() == live_db:
            raise RuntimeError(
                f"CRITICAL TEST ISOLATION FAILURE: Attempted to connect to live database at {target}! "
                f"Tests MUST use an isolated temporary database via SCAMSHIELD_DB_PATH."
            )
    return target


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Creates a new thread-safe SQLite connection with foreign keys and WAL enabled."""
    target_path = Path(db_path) if db_path is not None else get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection(db_path=db_path)
    try:
        with conn:
            # Users table (Items 1, 2, 3)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    is_verified INTEGER DEFAULT 0,
                    verification_code TEXT,
                    reset_token TEXT,
                    reset_expires REAL,
                    created_at REAL NOT NULL
                );
            """)

            # User Scan History table with Row-Level Security isolation (Item 10)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    preview_text TEXT,
                    preview_url TEXT,
                    verdict TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    risk_band TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # Index on user_id for fast private history lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_scans_user_id
                ON user_scans(user_id, timestamp DESC);
            """)
    finally:
        conn.close()


def __getattr__(name: str) -> Any:
    """Module-level attribute lookup supporting dynamic DB_PATH resolution."""
    if name == "DB_PATH":
        return get_db_path()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Initialize database safely on import in production/dev (not during tests)
if os.getenv("SCAMSHIELD_TEST_MODE") != "1" and "pytest" not in sys.modules:
    try:
        init_db()
    except Exception:
        pass

