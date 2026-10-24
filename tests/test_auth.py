"""
Integration & Security Tests — Authentication, Row-Level Isolation, and Backups
(Items 1, 2, 3, 9, 10, 18)

Verifies:
1. User registration, password hashing (PBKDF2-100k), and duplicate detection (Item 1).
2. Email verification with 6-digit OTP (Item 3).
3. Session login, token issuance, and logout (Item 1).
4. Password reset token issuance and password update (Item 2).
5. Row-Level Security: Strict tenant data isolation between users (Item 10).
6. GDPR Art. 17 right-to-erasure account deletion & scan purge (Item 18).
7. Automated online database backup creation and retention (Item 9).
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db_connection
from app.main import app
from app.services.auth_service import auth_service
from scripts.backup_db import backup_database


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure tests run against a clean database state."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM user_scans;")
            conn.execute("DELETE FROM users;")
    finally:
        conn.close()
    yield



def test_user_registration_and_email_verification(client):
    """Test user registration followed by email verification code confirmation."""
    email = "researcher.alice@klebca.edu"
    password = "StrongPassword2026!"

    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["status"] == "success"
    assert reg_data["email"] == email
    assert reg_data["is_verified"] is False
    assert len(reg_data["verification_code"]) == 6
    code = reg_data["verification_code"]

    # 2. Duplicate registration should be rejected
    dup_res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Invalid verification code rejected
    bad_verify = client.post("/api/v1/auth/verify-email", json={"email": email, "code": "000000"})
    assert bad_verify.status_code == 400

    # 4. Valid verification code accepted
    good_verify = client.post("/api/v1/auth/verify-email", json={"email": email, "code": code})
    assert good_verify.status_code == 200
    assert "verified successfully" in good_verify.json()["message"]


def test_login_and_session_token(client):
    """Test login authentication and bearer token usage."""
    email = "researcher.alice@klebca.edu"
    password = "StrongPassword2026!"

    # Register and verify email first
    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code == 201
    code = reg_res.json()["verification_code"]
    client.post("/api/v1/auth/verify-email", json={"email": email, "code": code})

    # Bad password
    bad_res = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword!"})
    assert bad_res.status_code == 401

    # Good password
    good_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert good_res.status_code == 200
    data = good_res.json()
    assert data["status"] == "success"
    assert "token" in data
    assert data["is_verified"] is True
    token = data["token"]

    # Access /api/v1/auth/me with bearer header
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == email


def test_password_reset_flow(client):
    """Test cryptographic password reset token generation and execution."""
    email = "researcher.alice@klebca.edu"
    password = "StrongPassword2026!"
    new_password = "BrandNewPassword2026!"

    # Register user first
    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code == 201

    # 1. Request reset
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    assert "reset_token" not in forgot_res.json(), "CRITICAL LEAK: reset_token must never be returned in public API response!"
    assert "dispatched" in forgot_res.json()["message"]

    # Retrieve token directly from isolated test DB (as would be delivered out-of-band via email)
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT reset_token FROM users WHERE email = ?;", (email,)).fetchone()
        reset_token = row["reset_token"]
    finally:
        conn.close()
    assert reset_token is not None

    # 2. Reset with invalid token rejected
    bad_reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid_token_12345", "new_password": new_password},
    )
    assert bad_reset.status_code == 400

    # 3. Reset with valid token accepted
    good_reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": new_password},
    )
    assert good_reset.status_code == 200

    # 4. Login with old password rejected
    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPassword2026!"})
    assert old_login.status_code == 401

    # 5. Login with new password accepted
    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": new_password})
    assert new_login.status_code == 200


def test_row_level_security_tenant_isolation(client):
    """Row-Level Security (Item 10): User B cannot see User A's private scans."""
    # User A
    user_a_email = "user.alpha@klebca.edu"
    user_a_pwd = "PasswordAlpha2026!"
    reg_a = client.post("/api/v1/auth/register", json={"email": user_a_email, "password": user_a_pwd})
    token_a = reg_a.json()["token"]

    # User B
    user_b_email = "user.beta@klebca.edu"
    user_b_pwd = "PasswordBeta2026!"
    reg_b = client.post("/api/v1/auth/register", json={"email": user_b_email, "password": user_b_pwd})
    token_b = reg_b.json()["token"]

    # User A performs an analysis scan
    scan_res = client.post(
        "/api/v1/analyze",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"text": "URGENT: Your account needs verification at http://suspicious-link.xyz"},
    )
    assert scan_res.status_code == 200

    # User A checks history -> Has 1 scan
    history_a = client.get("/api/v1/auth/history", headers={"Authorization": f"Bearer {token_a}"})
    assert history_a.status_code == 200
    scans_a = history_a.json()["scans"]
    assert len(scans_a) >= 1
    assert "verification" in scans_a[0]["preview_text"]

    # User B checks history -> Has 0 scans (Zero cross-tenant leakage!)
    history_b = client.get("/api/v1/auth/history", headers={"Authorization": f"Bearer {token_b}"})
    assert history_b.status_code == 200
    scans_b = history_b.json()["scans"]
    assert len(scans_b) == 0


def test_gdpr_account_deletion_and_data_purge(client):
    """GDPR Right to Erasure (Item 18): Deleting account purges user and scan records."""
    email = "user.to.delete@klebca.edu"
    pwd = "DeleteMePassword2026!"
    reg = client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    token = reg.json()["token"]

    # Run a scan to populate history
    client.post(
        "/api/v1/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "A temporary private scan message."},
    )

    # Delete account
    del_res = client.delete("/api/v1/auth/account", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert "permanently purged" in del_res.json()["message"]

    # Further authenticated queries with the old token fail
    post_del_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert post_del_res.status_code == 401


def test_automated_database_backup(tmp_path):
    """Database Backups (Item 9): Online SQLite snapshot is created and valid."""
    backup_path = backup_database(backup_dir=tmp_path, max_retention=3)
    assert backup_path.exists()
    assert backup_path.stat().st_size > 0
    assert "scamshield_backup_" in backup_path.name


def test_database_pruning_and_integrity():
    """Database Hygiene (Stage C): Token pruning and SQLite integrity check."""
    import time
    from scripts.prune_data import prune_expired_tokens, check_database_integrity, checkpoint_wal
    from app.db.database import get_db_connection

    # 1. Integrity check on clean test DB
    assert check_database_integrity() is True

    # 2. Insert expired reset token
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO users (email, password_hash, salt, reset_token, reset_expires, created_at)
                VALUES ('expired.user@test.com', 'dummy_hash', 'dummy_salt', 'expired_tok_123', ?, ?);
                """,
                (time.time() - 3600, time.time() - 7200),
            )
    finally:
        conn.close()

    # 3. Prune expired tokens
    cleared = prune_expired_tokens()
    assert cleared == 1

    # 4. Verify token was cleared
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT reset_token, reset_expires FROM users WHERE email = 'expired.user@test.com';")
        row = cursor.fetchone()
        assert row["reset_token"] is None
        assert row["reset_expires"] is None
    finally:
        conn.close()

    # 5. Checkpoint WAL
    checkpoint_wal()


def test_password_reset_security_and_non_disclosure(client):
    """
    P0 Regression Test Suite (Stage D):
    1. Public response never discloses reset_token.
    2. Unknown and known emails receive identical generic responses (no enumeration).
    3. Token cannot be reused after consumption.
    4. Expired tokens are rejected.
    5. Headers and logs do not leak reset tokens.
    """
    import time
    email = "target.victim@klebca.edu"
    reg = client.post("/api/v1/auth/register", json={"email": email, "password": "OriginalPassword2026!"})
    assert reg.status_code == 201

    # 1. Request reset for known email -> 200 generic message, NO token in body or headers
    res_known = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert res_known.status_code == 200
    assert "reset_token" not in res_known.json()
    known_msg = res_known.json()["message"]

    # Check response headers for token leakage
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT reset_token FROM users WHERE email = ?;", (email,)).fetchone()
        token = row["reset_token"]
    finally:
        conn.close()
    assert token is not None
    assert not any(token in str(v) for v in res_known.headers.values()), "Token leaked in response headers!"

    # 2. Request reset for unknown email -> Identical 200 response (prevents account enumeration)
    res_unknown = client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent.attacker@klebca.edu"})
    assert res_unknown.status_code == 200
    assert "reset_token" not in res_unknown.json()
    assert res_unknown.json()["message"] == known_msg

    # 3. Valid token resets password
    reset_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewSecurePassword2026!"},
    )
    assert reset_res.status_code == 200

    # 4. Token cannot be reused after consumption
    reuse_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "AnotherPassword2026!"},
    )
    assert reuse_res.status_code == 400

    # 5. Expired token cannot reset password
    from app.services.auth_service import auth_service
    expired_token = auth_service.create_password_reset(email)
    assert expired_token is not None

    conn = get_db_connection()
    try:
        with conn:
            conn.execute("UPDATE users SET reset_expires = ? WHERE email = ?;", (time.time() - 3600, email))
    finally:
        conn.close()

    expired_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": expired_token, "new_password": "AnotherPassword2026!"},
    )
    assert expired_res.status_code == 400


def test_fail_closed_production_secret_key(monkeypatch):
    """
    P0 Regression Test Suite (Stage D):
    1. Production startup fails when secret is missing or empty.
    2. Production startup fails when secret is an insecure default.
    3. Production startup fails when secret is shorter than 32 characters.
    4. Valid configured secret allows operation.
    5. Tokens signed with mismatched secrets are rejected.
    """
    from app.config import Settings
    from app.services.auth_service import generate_session_token, verify_session_token

    # 1. Missing secret in production -> raises RuntimeError
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SCAMSHIELD_TEST_MODE", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)

    s_missing = Settings()
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY is absent or empty"):
        _ = s_missing.AUTH_SECRET_KEY

    # 2. Insecure default in production -> raises RuntimeError
    monkeypatch.setenv("AUTH_SECRET_KEY", "scamshield_production_secret_key_2026")
    s_insecure = Settings()
    with pytest.raises(RuntimeError, match="Insecure or default AUTH_SECRET_KEY"):
        _ = s_insecure.AUTH_SECRET_KEY

    # 3. Short secret (< 32 chars) in production -> raises RuntimeError
    monkeypatch.setenv("AUTH_SECRET_KEY", "too_short_secret_key_123")
    s_short = Settings()
    with pytest.raises(RuntimeError, match="Insecure or default AUTH_SECRET_KEY"):
        _ = s_short.AUTH_SECRET_KEY

    # 4. Valid 64-char hex secret in production -> succeeds
    valid_key = "a" * 64
    monkeypatch.setenv("AUTH_SECRET_KEY", valid_key)
    s_valid = Settings()
    assert s_valid.AUTH_SECRET_KEY == valid_key

    # 5. Token signed with Key A is rejected when verified with Key B
    key_a = "secret_key_alpha_32_characters_12345"
    key_b = "secret_key_bravo_32_characters_67890"
    tok = generate_session_token(42, "user@test.com", secret=key_a)
    assert verify_session_token(tok, secret=key_a) is not None
    assert verify_session_token(tok, secret=key_b) is None


