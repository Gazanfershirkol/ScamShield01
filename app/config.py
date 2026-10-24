"""
ScamShield AI — Application Configuration Module

Provides typed configuration settings and environment variable management
for the ScamShield AI detection engine, API service, and evaluation pipeline.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Set


BASE_DIR = Path(__file__).resolve().parent.parent

INSECURE_SECRET_DEFAULTS: Set[str] = {
    "scamshield_production_secret_key_2026",
    "CHANGE_THIS_TO_A_CRYPTOGRAPHICALLY_RANDOM_64_CHAR_HEX_KEY",
    "secret",
    "secretkey",
    "password",
    "changeme",
    "default",
}


@dataclass(frozen=True)
class Settings:
    """Immutable application settings and security boundaries."""

    # Application identity
    APP_NAME: str = os.getenv("APP_NAME", "ScamShield AI")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")

    # Security input payload limits
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
    MAX_URL_LENGTH: int = int(os.getenv("MAX_URL_LENGTH", "2048"))

    # Verdict & risk score thresholds (0-100 scale)
    VERDICT_SCAM_THRESHOLD: int = int(os.getenv("VERDICT_SCAM_THRESHOLD", "75"))
    VERDICT_REVIEW_THRESHOLD: int = int(os.getenv("VERDICT_REVIEW_THRESHOLD", "35"))

    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    TOKEN_EXPIRY_SECONDS: int = int(os.getenv("TOKEN_EXPIRY_SECONDS", "86400"))

    @property
    def AUTH_SECRET_KEY(self) -> str:
        """
        Cryptographic signing secret for bearer session tokens.
        Enforces strict fail-closed validation:
        - In production mode (APP_ENV='production'), startup aborts immediately if AUTH_SECRET_KEY
          is missing, empty, shorter than 32 characters, or matches any known insecure default.
        - In test mode, returns explicit isolated test secret.
        - In development mode, falls back to a development secret.
        """
        app_env = os.getenv("APP_ENV", self.APP_ENV).lower().strip()
        is_testing = (
            os.getenv("SCAMSHIELD_TEST_MODE") == "1"
            or "PYTEST_CURRENT_TEST" in os.environ
            or "pytest" in sys.modules
        )

        val = os.getenv("AUTH_SECRET_KEY", "").strip()

        if app_env == "production":
            if not val:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: AUTH_SECRET_KEY is absent or empty in production mode! "
                    "Startup aborted. You must configure a cryptographically random secret (min 32 characters)."
                )
            if val in INSECURE_SECRET_DEFAULTS or len(val) < 32:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Insecure or default AUTH_SECRET_KEY detected in production mode! "
                    "Startup aborted. You must configure a high-entropy secret (min 32 characters)."
                )
            return val

        if is_testing:
            return val if val else "scamshield_isolated_test_secret_key_2026"

        # Development fallback
        return val if val else "scamshield_dev_secret_not_for_production_2026"

    # Production Server & Networking Settings (Stage B Hardening)
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CORS_ORIGINS_RAW: str = os.getenv("CORS_ORIGINS", "*")

    # Trusted reverse proxy configuration (Stage A security)
    TRUSTED_PROXIES_RAW: str = os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1,testclient")

    @property
    def CORS_ORIGINS(self) -> list[str]:
        """Parsed list of allowed CORS origins."""
        raw = os.getenv("CORS_ORIGINS", self.CORS_ORIGINS_RAW)
        return [o.strip() for o in raw.split(",") if o.strip()]


    # Filesystem paths
    BASE_DIR: Path = BASE_DIR
    MODEL_DIR: Path = BASE_DIR / "app" / "models"
    MODEL_PATH: Path = BASE_DIR / "app" / "models" / "text_model.joblib"
    EVALUATION_META_PATH: Path = BASE_DIR / "app" / "models" / "evaluation_meta.json"
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    DATA_DIR: Path = BASE_DIR / "data"
    DEFAULT_DB_PATH: Path = BASE_DIR / "data" / "scamshield.db"
    DEFAULT_BACKUP_DIR: Path = BASE_DIR / "data" / "backups"

    @property
    def DB_PATH(self) -> Path:
        """Active SQLite database path, supporting environment overrides."""
        override = os.getenv("SCAMSHIELD_DB_PATH")
        if override:
            return Path(override)
        return self.DEFAULT_DB_PATH

    @property
    def BACKUP_DIR(self) -> Path:
        """Active database backup directory, supporting environment overrides."""
        override = os.getenv("SCAMSHIELD_BACKUP_DIR")
        if override:
            return Path(override)
        return self.DEFAULT_BACKUP_DIR

    @property
    def TRUSTED_PROXIES(self) -> Set[str]:
        """Set of trusted upstream reverse proxies allowed to forward client IPs."""
        raw = os.getenv("TRUSTED_PROXIES", self.TRUSTED_PROXIES_RAW)
        return {p.strip() for p in raw.split(",") if p.strip()}



# Singleton configuration instance
settings = Settings()

