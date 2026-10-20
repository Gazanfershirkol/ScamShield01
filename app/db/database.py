"""
ScamShield AI — Database & Repository Layer (Items 1, 9, 10, 18)

Provides a lightweight, zero-dependency SQLite repository layer
with WAL mode, foreign key enforcement, and strict user data isolation.
"""

from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional

from app.config import settings

# Database file location
DB_PATH = settings.BASE_DIR / "data" / "scamshield.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db_connection() -> sqlite3.Connection:
    """Creates a new thread-safe SQLite connection with foreign keys and WAL enabled."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db() -> None:
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
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


# Ensure database is initialized on import
init_db()
