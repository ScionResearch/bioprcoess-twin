"""
Main FastAPI application entry point.
Configures middleware, CORS, error handlers, and routes.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

from .config import settings
from .routers import batches, calibrations, inoculations, media, samples, failures, closures, auth

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Electronic lab notebook API for Pichia pastoris fermentation campaigns",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed messages."""
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        error_dict = error.copy()
        # Convert any non-serializable types to strings
        if 'input' in error_dict and isinstance(error_dict['input'], bytes):
            error_dict['input'] = error_dict['input'].decode('utf-8', errors='replace')
        errors.append(error_dict)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": 422,
            "message": "Validation error",
            "detail": errors,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    """Handle database integrity constraint violations."""
    logger.error(f"IntegrityError: {exc}")

    # Parse common constraint violations
    error_msg = str(exc.orig)
    message = "Database constraint violation"

    if "unique_batch_per_phase" in error_msg:
        message = "Batch number already exists in this phase"
    elif "one_media_prep_per_batch" in error_msg:
        message = "Media preparation already exists for this batch"
    elif "one_inoculation_per_batch" in error_msg:
        message = "Inoculation already recorded for this batch"
    elif "one_closure_per_batch" in error_msg:
        message = "Batch closure already recorded"

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "status": "error",
            "code": 409,
            "message": message,
            "detail": {"database_error": error_msg},
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions."""
    logger.exception(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "code": 500,
            "message": "Internal server error",
            "detail": {"error": str(exc)} if settings.DEBUG else None,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """Kubernetes readiness probe."""
    # TODO: Add database connection check
    return {"status": "ready"}


# ============================================================================
# ROUTERS
# ============================================================================

# Authentication routes (no prefix, public)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["auth"])

# Batch management routes
app.include_router(batches.router, prefix=settings.API_V1_PREFIX, tags=["batches"])
app.include_router(calibrations.router, prefix=settings.API_V1_PREFIX, tags=["calibrations"])
app.include_router(media.router, prefix=settings.API_V1_PREFIX, tags=["media"])
app.include_router(inoculations.router, prefix=settings.API_V1_PREFIX, tags=["inoculations"])
app.include_router(samples.router, prefix=settings.API_V1_PREFIX, tags=["samples"])
app.include_router(failures.router, prefix=settings.API_V1_PREFIX, tags=["failures"])
app.include_router(closures.router, prefix=settings.API_V1_PREFIX, tags=["closures"])


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info(f"API documentation available at {settings.API_V1_PREFIX}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": "/health"
    }
