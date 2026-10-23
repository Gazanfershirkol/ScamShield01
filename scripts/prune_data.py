"""
ScamShield AI — Database Maintenance & Token Expiry Pruning Utility

Performs routine operational database hygiene:
1. Prunes expired password reset tokens whose expiration timestamp has lapsed.
2. Checks SQLite database integrity via PRAGMA integrity_check.
3. Checkpoints WAL journal to prevent unbounded file growth.
"""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.database import get_db_connection, get_db_path


def prune_expired_tokens() -> int:
    """
    Clears reset_token and reset_expires for accounts where the token has expired.
    
    Returns:
        Number of expired reset records cleared.
    """
    now = time.time()
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                UPDATE users
                SET reset_token = NULL, reset_expires = NULL
                WHERE reset_expires IS NOT NULL AND reset_expires < ?;
                """,
                (now,),
            )
            return cursor.rowcount
    finally:
        conn.close()


def check_database_integrity() -> bool:
    """
    Runs SQLite integrity check to ensure database pages are not corrupted.
    
    Returns:
        True if database passes integrity check, False otherwise.
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute("PRAGMA integrity_check;")
        row = cursor.fetchone()
        result = row[0] if row else "unknown"
        return result == "ok"
    finally:
        conn.close()


def checkpoint_wal() -> None:
    """Forces a PASSIVE WAL checkpoint to recycle write-ahead log pages."""
    conn = get_db_connection()
    try:
        conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
    finally:
        conn.close()


if __name__ == "__main__":
    db_file = get_db_path()
    print(f"[*] Starting ScamShield database maintenance on {db_file}...")
    
    # 1. Integrity check
    is_ok = check_database_integrity()
    if is_ok:
        print("[+] Integrity check: OK")
    else:
        print("[!] Integrity check: FAILED (Possible corruption)")
        sys.exit(1)

    # 2. Prune expired tokens
    cleared = prune_expired_tokens()
    print(f"[+] Expired password reset tokens cleared: {cleared}")

    # 3. WAL Checkpoint
    checkpoint_wal()
    print("[+] WAL checkpoint complete.")
    print("[*] Maintenance successfully finished.")
