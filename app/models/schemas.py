"""
Data schemas for OCR API.

This module defines the request and response models for the OCR service.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TextLine(BaseModel):
    """A single text line with its bounding box and confidence."""
    text: str = Field(..., description="Recognized text content")
    box: List[List[float]] = Field(..., description="Bounding box coordinates")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Recognition confidence (0-1)")


class OcrOptionsRequest(BaseModel):
    """OCR recognition options."""
    lang: str = Field(default="ch", description="Language code (ch, en, ch_traditional, etc.)")
    enable_table: bool = Field(default=False, description="Enable table recognition")
    enable_formula: bool = Field(default=False, description="Enable formula recognition")
    return_details: bool = Field(default=True, description="Return detailed line information")


class OcrData(BaseModel):
    """OCR recognition result data."""
    text: str = Field(..., description="Full recognized text (all lines concatenated)")
    lines: List[TextLine] = Field(default_factory=list, description="Individual text lines with details")
    elapsed_time: float = Field(..., ge=0.0, description="Processing time in seconds")
    engine: str = Field(..., description="OCR engine used for recognition")
    requested_engine: Optional[str] = Field(None, description="Engine requested by user (may differ from engine if fallback occurred)")
    fallback_used: bool = Field(False, description="Whether a fallback engine was used")


class OcrResponse(BaseModel):
    """Standard OCR API response."""
    success: bool = Field(..., description="Whether recognition was successful")
    data: Optional[OcrData] = Field(None, description="OCR result data (present when success=True)")
    error: Optional[str] = Field(None, description="Error message (present when success=False)")


class OcrRequestBase64(BaseModel):
    """OCR request with base64 encoded image."""
    image: Optional[str] = Field(
        default=None,
        description="Base64 encoded image data URL (e.g., 'data:image/jpeg;base64,...')"
    )
    engine: Optional[str] = Field(
        default=None,
        description="OCR engine to use. Default: paddleocr"
    )
    options: Optional[OcrOptionsRequest] = Field(
        default=None,
        description="OCR recognition options"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status (ok/error)")
    service: str = Field(default="ocr_py", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    engines: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Available OCR engines")


class EnginesListResponse(BaseModel):
    """Response listing available OCR engines."""
    engines: Dict[str, Dict[str, Any]] = Field(..., description="Available engines with status")
    default: str = Field(..., description="Default engine name")
