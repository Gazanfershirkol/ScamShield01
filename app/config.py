"""
ScamShield AI — Application Configuration Module

Provides typed configuration settings and environment variable management
for the ScamShield AI detection engine, API service, and evaluation pipeline.
"""

from dataclasses import dataclass
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


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

    # Production SaaS Settings (Items 1, 8, 9)
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    AUTH_SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "scamshield_production_secret_key_2026")
    TOKEN_EXPIRY_SECONDS: int = int(os.getenv("TOKEN_EXPIRY_SECONDS", "86400"))

    # Filesystem paths
    BASE_DIR: Path = BASE_DIR
    MODEL_DIR: Path = BASE_DIR / "app" / "models"
    MODEL_PATH: Path = BASE_DIR / "app" / "models" / "text_model.joblib"
    EVALUATION_META_PATH: Path = BASE_DIR / "app" / "models" / "evaluation_meta.json"
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = BASE_DIR / "data" / "scamshield.db"
    BACKUP_DIR: Path = BASE_DIR / "data" / "backups"



# Singleton configuration instance
settings = Settings()
