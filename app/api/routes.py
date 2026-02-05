"""
API routes for OCR service.

This module defines the HTTP endpoints for the OCR service.
Supports multiple OCR engines with automatic fallback.
"""

import logging
import tempfile
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, UploadFile, Request
from fastapi.responses import JSONResponse

from app.models.schemas import (
    OcrResponse,
    OcrData,
    OcrRequestBase64,
    OcrOptionsRequest,
    HealthResponse,
    EnginesListResponse,
    TextLine,
)
from app.core.config import config
from app.core.engine_router import get_engine_router
from app.engines.base import OcrOptions
from app.engines.paddleocr_engine import PaddleOcrEngine
from app.engines.factory import EngineFactory
from app.utils.image import (
    decode_base64_image,
    save_temp_image,
    get_file_extension,
    cleanup_temp_file,
)


logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize OCR engines
_engine_initialized = False


def _init_engines():
    """Initialize OCR engines."""
    global _engine_initialized
    if _engine_initialized:
        return

    # Register PaddleOCR engine
    paddle_engine = PaddleOcrEngine()
    EngineFactory.register(paddle_engine)
    logger.info("PaddleOCR engine registered")

    # Additional engines can be registered here in the future
    # Example:
    # from app.engines.custom_engine import CustomEngine
    # custom_engine = CustomEngine()
    # EngineFactory.register(custom_engine)

    _engine_initialized = True


# Initialize engines on module load
_init_engines()

# Get engine router
engine_router = get_engine_router()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the service status and OCR engine availability.
    """
    engines_status = engine_router.list_engines()
    return HealthResponse(
        status="ok" if any(e["available"] for e in engines_status.values()) else "error",
        service=config.SERVICE_NAME,
        version=config.VERSION,
        engines=engines_status
    )


@router.get("/engines", response_model=EnginesListResponse)
async def list_engines() -> EnginesListResponse:
    """
    List all available OCR engines.

    Returns information about registered engines and their availability.
    """
    engines_status = engine_router.list_engines()
    return EnginesListResponse(
        engines=engines_status,
        default=engine_router.get_default_engine()
    )


@router.post("/ocr/recognize", response_model=OcrResponse)
async def recognize_image(
    request: Request
) -> OcrResponse:
    """
    OCR recognition endpoint.

    Accepts image data in two formats:
    1. Base64 data URL in JSON body: {"image": "data:image/jpeg;base64,..."}
    2. File upload via multipart/form-data

    Supports engine selection via `engine` parameter:
    - paddleocr: Local PaddleOCR engine (default, free)

    Additional engines can be added in the future through the engine architecture.

    Returns structured JSON with recognized text, line details, and metadata.
    """
    # Check content type to determine input format
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # JSON with Base64 data URL
        return await _recognize_from_base64(request)
    elif "multipart/form-data" in content_type:
        # File upload
        return await _recognize_from_upload(request)
    else:
        return OcrResponse(
            success=False,
            data=None,
            error=f"Unsupported content type: {content_type}. Use application/json or multipart/form-data"
        )


async def _recognize_from_base64(request: Request) -> OcrResponse:
    """Handle Base64 encoded image recognition."""
    try:
        # Parse JSON body
        body = await request.json()
        req_data = OcrRequestBase64(**body)

        # Validate required image field
        if not req_data.image:
            return OcrResponse(
                success=False,
                data=None,
                error="Missing required field: 'image'"
            )

        # Get OCR options
        ocr_options = OcrOptions(
            lang=req_data.options.lang if req_data.options else "ch",
            enable_table=req_data.options.enable_table if req_data.options else False,
            enable_formula=req_data.options.enable_formula if req_data.options else False,
            return_details=req_data.options.return_details if req_data.options else True,
        )

        # Decode base64 image
        image_bytes, mime_type = decode_base64_image(req_data.image)
        extension = get_file_extension(mime_type)

        # Save to temp file
        temp_path = save_temp_image(image_bytes, extension)

        try:
            # Perform OCR with engine routing
            result = engine_router.recognize(
                temp_path,
                ocr_options,
                engine_name=req_data.engine,
                enable_fallback=True
            )

            if result.success:
                return OcrResponse(
                    success=True,
                    data=OcrData(
                        text=result.text,
                        lines=[TextLine(**line) for line in result.lines],
                        elapsed_time=result.elapsed_time,
                        engine=result.engine,
                        requested_engine=result.requested_engine,
                        fallback_used=result.fallback_used
                    ),
                    error=None
                )
            else:
                return OcrResponse(
                    success=False,
                    data=None,
                    error=result.error or "Unknown error"
                )
        finally:
            # Cleanup temp file
            cleanup_temp_file(temp_path)

    except ValueError as e:
        return OcrResponse(success=False, data=None, error=str(e))
    except Exception as e:
        logger.error(f"Base64 recognition failed: {e}")
        return OcrResponse(success=False, data=None, error=f"Processing failed: {str(e)}")


async def _recognize_from_upload(request: Request) -> OcrResponse:
    """Handle file upload recognition."""
    try:
        # Parse multipart form data
        form = await request.form()
        if "image" not in form:
            return OcrResponse(success=False, data=None, error="Missing 'image' field in form data")

        file: UploadFile = form["image"]

        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > config.MAX_UPLOAD_SIZE:
            return OcrResponse(
                success=False,
                data=None,
                error=f"File too large. Maximum size: {config.MAX_UPLOAD_SIZE} bytes"
            )

        # Get engine parameter
        engine_name = form.get("engine")
        if engine_name:
            engine_name = str(engine_name)

        # Get options
        lang = form.get("lang", "ch")
        return_details = form.get("return_details", "true") == "true"

        # Save to temp file
        extension = "." + file.filename.split(".")[-1] if file.filename else ".jpg"
        temp_path = save_temp_image(content, extension)

        try:
            # Create OCR options
            ocr_options = OcrOptions(
                lang=str(lang),
                return_details=bool(return_details),
            )

            # Perform OCR with engine routing
            result = engine_router.recognize(
                temp_path,
                ocr_options,
                engine_name=engine_name,
                enable_fallback=True
            )

            if result.success:
                return OcrResponse(
                    success=True,
                    data=OcrData(
                        text=result.text,
                        lines=[TextLine(**line) for line in result.lines],
                        elapsed_time=result.elapsed_time,
                        engine=result.engine,
                        requested_engine=result.requested_engine,
                        fallback_used=result.fallback_used
                    ),
                    error=None
                )
            else:
                return OcrResponse(
                    success=False,
                    data=None,
                    error=result.error or "Unknown error"
                )
        finally:
            # Cleanup temp file
            cleanup_temp_file(temp_path)

    except Exception as e:
        logger.error(f"File upload recognition failed: {e}")
        return OcrResponse(success=False, data=None, error=f"Processing failed: {str(e)}")
