"""
ScamShield AI — Authentication & Security Service (Items 1, 2, 3, 10, 18)

Implements PBKDF2-HMAC-SHA256 password hashing, signed HMAC bearer session tokens,
email verification, password reset flows, and row-level data isolation.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.db.database import get_db_connection

# PBKDF2 configuration
PBKDF2_ITERATIONS = 100_000
TOKEN_SECRET = getattr(settings, "AUTH_SECRET_KEY", "scamshield_production_secret_key_2026")
TOKEN_EXPIRY_SECONDS = 86400  # 24 hours


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return key.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Constant-time verification of password against stored PBKDF2 hash."""
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, expected_hash)


def generate_session_token(user_id: int, email: str) -> str:
    """Generates a tamper-proof signed bearer session token."""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": time.time() + TOKEN_EXPIRY_SECONDS,
        "iat": time.time(),
    }
    raw_payload = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    signature = hmac.new(
        TOKEN_SECRET.encode("utf-8"),
        raw_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{raw_payload}.{signature}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifies and decodes a bearer session token. Returns payload dict or None."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        raw_payload, signature = parts
        expected_sig = hmac.new(
            TOKEN_SECRET.encode("utf-8"),
            raw_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None

        payload_bytes = base64.urlsafe_b64decode(raw_payload.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        if time.time() > payload.get("exp", 0):
            return None

        return payload
    except Exception:
        return None


class AuthService:
    """Encapsulates user authentication, verification, and row-level isolated storage."""

    @staticmethod
    def register_user(email: str, password: str) -> Dict[str, Any]:
        """Registers a new user account with simulated email verification code."""
        email_clean = email.strip().lower()
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        pwd_hash, salt = hash_password(password)
        verif_code = f"{secrets.randbelow(900000) + 100000}"  # 6-digit numeric OTP

        conn = get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, salt, is_verified, verification_code, created_at)
                    VALUES (?, ?, ?, 0, ?, ?);
                    """,
                    (email_clean, pwd_hash, salt, verif_code, time.time()),
                )
                user_id = cursor.lastrowid
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                raise ValueError("An account with this email address already exists.")
            raise
        finally:
            conn.close()

        token = generate_session_token(user_id, email_clean)
        return {
            "user_id": user_id,
            "email": email_clean,
            "is_verified": False,
            "verification_code": verif_code,
            "token": token,
        }

    @staticmethod
    def verify_email(email: str, code: str) -> bool:
        """Verifies an email using the issued 6-digit code."""
        email_clean = email.strip().lower()
        conn = get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, verification_code FROM users WHERE email = ?;",
                    (email_clean,),
                )
                row = cursor.fetchone()
                if not row or row["verification_code"] != code.strip():
                    return False
                conn.execute(
                    "UPDATE users SET is_verified = 1, verification_code = NULL WHERE id = ?;",
                    (row["id"],),
                )
                return True
        finally:
            conn.close()

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Validates credentials and returns session token and profile if valid."""
        email_clean = email.strip().lower()
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, password_hash, salt, is_verified FROM users WHERE email = ?;",
                (email_clean,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            if not verify_password(password, row["salt"], row["password_hash"]):
                return None

            token = generate_session_token(row["id"], row["email"])
            return {
                "user_id": row["id"],
                "email": row["email"],
                "is_verified": bool(row["is_verified"]),
                "token": token,
            }
        finally:
            conn.close()

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Fetches sanitized user profile."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, is_verified, created_at FROM users WHERE id = ?;",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "email": row["email"],
                "is_verified": bool(row["is_verified"]),
                "created_at": row["created_at"],
            }
        finally:
            conn.close()

    @staticmethod
    def create_password_reset(email: str) -> Optional[str]:
        """Generates a secure password reset token expiring in 1 hour."""
        email_clean = email.strip().lower()
        reset_token = secrets.token_urlsafe(24)
        expires = time.time() + 3600  # 1 hour
        conn = get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM users WHERE email = ?;",
                    (email_clean,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                conn.execute(
                    "UPDATE users SET reset_token = ?, reset_expires = ? WHERE id = ?;",
                    (reset_token, expires, row["id"]),
                )
                return reset_token
        finally:
            conn.close()

    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """Resets user password if token is valid and unexpired."""
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        pwd_hash, salt = hash_password(new_password)
        conn = get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, reset_expires FROM users WHERE reset_token = ?;",
                    (token.strip(),),
                )
                row = cursor.fetchone()
                if not row or time.time() > row["reset_expires"]:
                    return False

                conn.execute(
                    """
                    UPDATE users 
                    SET password_hash = ?, salt = ?, reset_token = NULL, reset_expires = NULL 
                    WHERE id = ?;
                    """,
                    (pwd_hash, salt, row["id"]),
                )
                return True
        finally:
            conn.close()

    @staticmethod
    def delete_account(user_id: int) -> bool:
        """
        GDPR Right-to-Erasure (Item 18):
        Permanently deletes user account and cascades deletion of all scan history.
        """
        conn = get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Row-Level Security: User Scan History (Item 10)
    # -------------------------------------------------------------------------

    @staticmethod
    def record_scan(
        user_id: int,
        preview_text: Optional[str],
        preview_url: Optional[str],
        verdict: str,
        risk_score: float,
        confidence: float,
        risk_band: str,
    ) -> None:
        """Records an authenticated user scan event."""
        # Sanitize text preview to first 120 chars
        clean_preview_text = preview_text[:120].strip() if preview_text else None
        clean_preview_url = preview_url[:120].strip() if preview_url else None

        conn = get_db_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO user_scans 
                    (user_id, timestamp, preview_text, preview_url, verdict, risk_score, confidence, risk_band)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        user_id,
                        time.time(),
                        clean_preview_text,
                        clean_preview_url,
                        verdict,
                        risk_score,
                        confidence,
                        risk_band,
                    ),
                )
        finally:
            conn.close()

    @staticmethod
    def get_user_scans(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Row-Level Security Enforcement:
        Strictly returns scans belonging ONLY to the authenticated user_id.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, preview_text, preview_url, verdict, risk_score, confidence, risk_band
                FROM user_scans
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?;
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "preview_text": row["preview_text"],
                    "preview_url": row["preview_url"],
                    "verdict": row["verdict"],
                    "risk_score": row["risk_score"],
                    "confidence": row["confidence"],
                    "risk_band": row["risk_band"],
                }
                for row in rows
            ]
        finally:
            conn.close()


auth_service = AuthService()
