"""
ScamShield AI — Main FastAPI Application Service

Bootstraps the FastAPI web service, mounts the API v1 router, serves static frontend
assets, and configures cross-origin resource sharing (CORS).
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.auth_endpoints import router as auth_router
from app.api.endpoints import router as api_v1_router
from app.config import settings
from app.services.analytics import analytics_engine

from contextlib import asynccontextmanager
import logging

logger = logging.getLogger("scamshield")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warms ML model and underlying subsystems on startup to ensure zero-latency first requests."""
    try:
        from app.services.text_analyzer import get_text_analyzer
        get_text_analyzer()
    except Exception as exc:
        logger.warning(f"ML engine pre-warmup deferred: {exc}")
    yield


# Instantiate FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "ScamShield AI is an ultra-fast, explainable fraud and phishing detection system "
        "providing passive lexical URL analysis and calibrated TF-IDF text classification."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) for local and production access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Adds defensive HTTP security headers to all responses (Stage B Hardening)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


# Register API v1 endpoints routers
app.include_router(api_v1_router)
app.include_router(auth_router)

# Mount static asset directory if it exists
if settings.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serves the frontend dashboard index.html, or a fallback API discovery payload."""
    index_path = settings.STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(
        content={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "operational",
            "documentation": "/docs",
            "endpoints": {
                "analyze": f"{settings.API_V1_PREFIX}/analyze",
                "health": f"{settings.API_V1_PREFIX}/health",
                "evaluation": f"{settings.API_V1_PREFIX}/evaluation",
            },
        }
    )


@app.get("/privacy", include_in_schema=False)
async def serve_privacy():
    """Serves the Privacy Policy & Zero-Retention Guarantee page."""
    privacy_path = settings.STATIC_DIR / "privacy.html"
    if privacy_path.exists():
        return FileResponse(privacy_path)
    return JSONResponse(status_code=404, content={"detail": "Privacy policy not found"})


@app.get("/terms", include_in_schema=False)
async def serve_terms():
    """Serves the Terms of Service & Acceptable Use Policy page."""
    terms_path = settings.STATIC_DIR / "terms.html"
    if terms_path.exists():
        return FileResponse(terms_path)
    return JSONResponse(status_code=404, content={"detail": "Terms of service not found"})


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Custom exception handler serving high-tech 404 HTML for browsers, and JSON for API clients."""
    if exc.status_code == 404:
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            error_404_path = settings.STATIC_DIR / "404.html"
            if error_404_path.exists():
                return FileResponse(error_404_path, status_code=404)
        return JSONResponse(
            status_code=404,
            content={"detail": "Resource not found", "status_code": 404, "path": request.url.path},
            headers=exc.headers,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Global error tracking boundary (Item 15) capturing exceptions and returning sanitized incident IDs."""
    incident_id = analytics_engine.record_error(
        error_type=type(exc).__name__,
        path=request.url.path,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server security exception occurred.",
            "status_code": 500,
            "incident_id": incident_id,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=(settings.APP_ENV == "development"),
    )

