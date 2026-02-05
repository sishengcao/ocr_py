"""
OCR Service - Main Application Entry Point

A simple OCR service that provides text recognition from images.
Supports both Base64 encoded images and file uploads.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import config
from app.api.routes import router


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {config.SERVICE_NAME} v{config.VERSION}")
    logger.info(f"OCR Engine: PaddleOCR (lang={config.OCR_LANG})")
    yield
    logger.info(f"Shutting down {config.SERVICE_NAME}")


# Create FastAPI application
app = FastAPI(
    title=config.SERVICE_NAME,
    version=config.VERSION,
    description="OCR text recognition service using PaddleOCR",
    lifespan=lifespan
)

# Include routes
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "Invalid request format", "details": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower()
    )
