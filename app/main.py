"""FastAPI Application Main Entrypoint.

Configures application lifecycle, CORS middleware, global error handling,
and routes for the Semiconductor AI Early Warning Platform.
"""

from contextlib import asynccontextmanager
import logging
import os
import sys
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.api.v1 import api_v1_router
from app.api.v1.health import router as root_health_router

# Configure Structured Industrial Logging
logging.basicConfig(
    level=logging.INFO if not settings.APP_DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("semiconductor.platform")


def ensure_directories():
    """Ensure runtime folders exist."""
    dirs = [
        settings.DATA_RAW_DIR,
        settings.DATA_PROCESSED_DIR,
        settings.DATA_SYNTHETIC_DIR,
        settings.MODELS_DIR,
        "reports",
        "models/preprocessing",
        "models/metadata",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info("Storage and model directories verified.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown procedures."""
    logger.info(f"Initializing {settings.APP_NAME} [Environment: {settings.APP_ENV}]...")
    ensure_directories()
    try:
        init_db()
        logger.info("Database schemas loaded successfully.")
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")
    
    yield
    
    logger.info("Shutting down Semiconductor AI Platform gracefully...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade AI Early Warning & Decision Support Control Tower for Semiconductor Manufacturing.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception interceptor."""
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred within the fab analytics engine.",
            "path": request.url.path,
        },
    )


# Root Endpoints
@app.get("/", tags=["Root"])
async def root():
    """API Gateway Root Information."""
    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "fab_facility": settings.FAB_NAME,
        "api_v1_docs": "/docs",
        "health_check": "/health",
        "api_v1_health": f"{settings.API_V1_STR}/health",
    }


# Include Health Router at root level and API v1 level
app.include_router(root_health_router, prefix="/health", tags=["System Health"])
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.APP_DEBUG,
    )
