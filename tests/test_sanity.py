"""
ScamShield AI — Phase 1 Sanity Test Suite

Verifies Python version, critical dependency imports, configuration loading,
and project directory structure baseline.
"""

from pathlib import Path
import sys
import pytest


def test_python_version():
    """Verify that Python runtime is version 3.10 or newer."""
    assert sys.version_info >= (3, 10), (
        f"Python 3.10+ is required; detected version {sys.version_info.major}.{sys.version_info.minor}"
    )


def test_required_packages_importable():
    """Verify that all core project dependencies import without errors."""
    import fastapi
    import httpx
    import joblib
    import pydantic
    import sklearn
    import uvicorn

    assert fastapi.__name__ == "fastapi"
    assert pydantic.__name__ == "pydantic"
    assert sklearn.__name__ == "sklearn"
    assert uvicorn.__name__ == "uvicorn"
    assert httpx.__name__ == "httpx"
    assert joblib.__name__ == "joblib"


def test_config_settings_defaults():
    """Verify that app.config.Settings instantiates with specified default values."""
    from app.config import Settings, settings

    assert isinstance(settings, Settings)
    assert settings.APP_NAME == "ScamShield AI"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.VERDICT_SCAM_THRESHOLD == 75
    assert settings.VERDICT_REVIEW_THRESHOLD == 35
    assert settings.MAX_TEXT_LENGTH == 10000
    assert settings.MAX_URL_LENGTH == 2048
    assert settings.VERDICT_REVIEW_THRESHOLD < settings.VERDICT_SCAM_THRESHOLD


def test_project_directories_exist():
    """Verify that the required project directory scaffolding exists on disk."""
    from app.config import settings

    expected_directories = [
        settings.BASE_DIR / "app",
        settings.BASE_DIR / "app" / "api",
        settings.BASE_DIR / "app" / "services",
        settings.BASE_DIR / "app" / "models",
        settings.BASE_DIR / "app" / "static",
        settings.BASE_DIR / "data",
        settings.BASE_DIR / "data" / "raw",
        settings.BASE_DIR / "data" / "processed",
        settings.BASE_DIR / "data" / "synthetic",
        settings.BASE_DIR / "scripts",
        settings.BASE_DIR / "tests",
    ]

    for directory in expected_directories:
        assert directory.is_dir(), f"Expected directory does not exist: {directory}"
