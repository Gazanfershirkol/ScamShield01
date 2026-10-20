"""
ScamShield AI — Main FastAPI Application Service

Bootstraps the FastAPI web service, mounts the API v1 router, serves static frontend
assets, and configures cross-origin resource sharing (CORS).
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
