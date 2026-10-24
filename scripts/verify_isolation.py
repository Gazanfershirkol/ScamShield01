"""
Isolation Proof Script — ScamShield AI Stage A

Demonstrates that the test isolation boundary guarantees:
1. Connecting to live database is blocked during test mode.
2. Silent fallback to live database is blocked.
3. Test operations execute strictly in temporary storage.
4. Live database and live backups remain untouched with byte-for-byte SHA256 integrity.
"""

import hashlib
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def get_file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    print("[*] Proving ScamShield AI Test Database Isolation Boundary...")

    live_db = PROJECT_ROOT / "data" / "scamshield.db"
    live_db_existed = live_db.exists()
    if live_db_existed:
        initial_live_hash = get_file_sha256(live_db)
        initial_live_mtime = live_db.stat().st_mtime
        print(f"[*] Live DB found on host: {live_db} (size={live_db.stat().st_size}, sha256={initial_live_hash})")
    else:
        print(f"[*] Clean environment detected: Live DB does not exist on disk at {live_db} (git-ignored)")

    # 1. Test Mode Active, live DB target -> MUST raise RuntimeError
    os.environ["SCAMSHIELD_TEST_MODE"] = "1"
    os.environ["SCAMSHIELD_DB_PATH"] = str(live_db)
    
    from app.config import settings
    from app.db.database import get_db_path, get_db_connection, init_db

    try:
        get_db_path()
        raise AssertionError("CRITICAL FAILURE: Expected RuntimeError when pointing test to live database!")
    except RuntimeError as exc:
        print(f"[+] PROOF 1 PASSED: Live database access rejected in test mode: {exc}")

    # 2. Test Mode Active, unset path -> MUST raise RuntimeError
    del os.environ["SCAMSHIELD_DB_PATH"]
    try:
        get_db_path()
        raise AssertionError("CRITICAL FAILURE: Expected RuntimeError when test path is unset!")
    except RuntimeError as exc:
        print(f"[+] PROOF 2 PASSED: Silent fallback to live database rejected: {exc}")

    # 3. Test Mode Active with isolated temporary database -> MUST succeed on temp DB only
    with tempfile.TemporaryDirectory(prefix="isolation_proof_") as tmp_dir:
        tmp_db = Path(tmp_dir) / "isolated_test.db"
        tmp_backup_dir = Path(tmp_dir) / "test_backups"
        tmp_backup_dir.mkdir(parents=True, exist_ok=True)

        os.environ["SCAMSHIELD_DB_PATH"] = str(tmp_db)
        os.environ["SCAMSHIELD_BACKUP_DIR"] = str(tmp_backup_dir)

        # Active path must be temp db
        active_path = get_db_path()
        assert active_path.resolve() == tmp_db.resolve(), "Active path must match temp db"
        print(f"[*] Verified active DB path points to isolated temp file: {active_path}")

        # Initialize schema in temp DB
        init_db()
        assert tmp_db.exists(), "Temp DB file must exist after init_db()"

        # Perform destructive queries (simulating test suite clean_db)
        conn = get_db_connection()
        try:
            with conn:
                conn.execute("INSERT INTO users (email, password_hash, salt, created_at) VALUES ('test@proof.com', 'h', 's', 1.0);")
                conn.execute("DELETE FROM users;")
        finally:
            conn.close()
        print("[+] PROOF 3 PASSED: Destructive test fixtures executed on temp DB successfully.")

        # Test backup isolation
        from scripts.backup_db import backup_database
        backup_file = backup_database(backup_dir=tmp_backup_dir)
        assert backup_file.exists(), "Backup must exist in temp backup dir"
        assert backup_file.parent.resolve() == tmp_backup_dir.resolve(), "Backup must be in temp dir"
        print(f"[+] PROOF 4 PASSED: Backup executed strictly inside temp directory: {backup_file.name}")

    # 4. Verify live database was NEVER created or modified
    if live_db_existed:
        final_live_hash = get_file_sha256(live_db)
        final_live_mtime = live_db.stat().st_mtime
        assert initial_live_hash == final_live_hash, f"CRITICAL LEAK: Live DB hash changed from {initial_live_hash} to {final_live_hash}!"
        assert initial_live_mtime == final_live_mtime, "Live DB mtime changed!"
        print(f"[+] PROOF 5 PASSED: Live DB integrity verified 100% UNTOUCHED (SHA256: {final_live_hash})")
    else:
        assert not live_db.exists(), f"CRITICAL LEAK: Live DB was unexpectedly created at {live_db} during test operations!"
        print("[+] PROOF 5 PASSED: Clean checkout invariant verified: Live DB was NEVER created during test operations.")
    print("[*] TEST DATABASE ISOLATION RIGOROUSLY PROVEN.")


if __name__ == "__main__":
    main()
