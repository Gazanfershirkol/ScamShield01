"""
Pytest configuration and global fixtures for ScamShield AI test suite.

Enforces strict test database isolation:
- Creates an isolated temporary directory for SQLite database and backup artifacts.
- Sets SCAMSHIELD_TEST_MODE, SCAMSHIELD_DB_PATH, and SCAMSHIELD_BACKUP_DIR before app imports.
- Initializes schema in the isolated test database.
- Guarantees that no test connects to or modifies the live database (data/scamshield.db).
- Cleans up temporary artifacts after the test session completes.
"""

import os
from pathlib import Path
import shutil
import tempfile
import pytest

# Allocate isolated temporary directory for test storage
_test_tmp_dir = tempfile.mkdtemp(prefix="scamshield_test_isolation_")
_test_db_path = Path(_test_tmp_dir) / "test_scamshield.db"
_test_backup_dir = Path(_test_tmp_dir) / "test_backups"
_test_backup_dir.mkdir(parents=True, exist_ok=True)

# Enforce environment overrides prior to application imports
os.environ["SCAMSHIELD_TEST_MODE"] = "1"
os.environ["SCAMSHIELD_DB_PATH"] = str(_test_db_path)
os.environ["SCAMSHIELD_BACKUP_DIR"] = str(_test_backup_dir)

# Ensure trusted proxies default includes testclient for Starlette TestClient requests
if "TRUSTED_PROXIES" not in os.environ:
    os.environ["TRUSTED_PROXIES"] = "127.0.0.1,::1,testclient"

from app.config import settings
from app.db.database import get_db_path, init_db


@pytest.fixture(scope="session", autouse=True)
def test_db_isolation():
    """
    Session-level fixture that initializes the isolated test database
    and verifies live database immunity.
    """
    # Initialize the temporary database schema
    init_db()

    # Verify that the active db path is indeed the temporary test database
    active_path = get_db_path()
    live_path = (settings.BASE_DIR / "data" / "scamshield.db").resolve()
    assert active_path.resolve() != live_path, "CRITICAL: Test suite is pointing to live database!"
    assert active_path.resolve() == _test_db_path.resolve(), "CRITICAL: Test suite is not using isolated test DB!"

    yield _test_db_path

    # Teardown temporary directory after session completes
    try:
        shutil.rmtree(_test_tmp_dir, ignore_errors=True)
    except Exception:
        pass
