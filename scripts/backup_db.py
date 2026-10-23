"""
ScamShield AI — Automated Database Backup Utility (Item 9)

Performs zero-downtime online SQLite backups using the native sqlite3 backup API.
Rotates backups to retain the most recent snapshots, preventing disk exhaustion.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys
from typing import Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.db.database import get_db_path

MAX_BACKUP_RETENTION = 10


def get_backup_dir() -> Path:
    """Returns the active backup directory, respecting environment overrides."""
    return settings.BACKUP_DIR


def backup_database(
    backup_dir: Optional[Path] = None,
    max_retention: int = MAX_BACKUP_RETENTION,
    db_path: Optional[Path] = None,
) -> Path:
    """
    Performs a consistent online snapshot of the ScamShield database.
    
    Returns:
        Path to the created backup snapshot.
    """
    target_db = Path(db_path) if db_path is not None else get_db_path()
    target_backup_dir = Path(backup_dir) if backup_dir is not None else get_backup_dir()

    is_testing = (
        os.getenv("SCAMSHIELD_TEST_MODE") == "1"
        or "PYTEST_CURRENT_TEST" in os.environ
        or "pytest" in sys.modules
    )
    if is_testing and backup_dir is None:
        live_backup_dir = (settings.BASE_DIR / "data" / "backups").resolve()
        if target_backup_dir.resolve() == live_backup_dir:
            raise RuntimeError(
                "CRITICAL TEST ISOLATION FAILURE: Attempted to write backups to live directory during test!"
            )

    if not target_db.exists():
        raise FileNotFoundError(f"Source database not found at {target_db}")

    target_backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = target_backup_dir / f"scamshield_backup_{timestamp}.db"

    # Connect to source and destination
    src_conn = sqlite3.connect(str(target_db))
    dst_conn = sqlite3.connect(str(backup_file))

    try:
        # Online snapshot without blocking ongoing transactions
        src_conn.backup(dst_conn, pages=100)
    finally:
        dst_conn.close()
        src_conn.close()

    # Prune old backups
    _prune_backups(target_backup_dir, max_retention)

    return backup_file



def _prune_backups(backup_dir: Path, max_retention: int) -> None:
    """Keeps the most recent snapshots and deletes older files."""
    backups = sorted(
        backup_dir.glob("scamshield_backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if len(backups) > max_retention:
        for stale in backups[max_retention:]:
            try:
                stale.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    print(f"[*] Initiating ScamShield AI database backup from {DB_PATH}...")
    dest = backup_database()
    print(f"[+] Backup successfully completed: {dest}")
    print(f"[+] Size: {dest.stat().st_size} bytes")
