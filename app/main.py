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

from app.api.endpoints import router as api_v1_router
from app.config import settings

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
)

# Configure Cross-Origin Resource Sharing (CORS) for local and competition UI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 endpoints router
app.include_router(api_v1_router)

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
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
