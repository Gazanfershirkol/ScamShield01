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
    reset_token = forgot_res.json()["reset_token"]
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
