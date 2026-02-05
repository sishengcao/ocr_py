"""
Image processing utilities.

This module provides utilities for handling different image input formats.
"""

import base64
import re
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def decode_base64_image(data: str) -> Tuple[bytes, str]:
    """
    Decode base64 encoded image data.

    Args:
        data: Base64 data URL string (e.g., "data:image/jpeg;base64,...")

    Returns:
        Tuple of (image_bytes, mime_type)

    Raises:
        ValueError: If data format is invalid
    """
    # Check for data URL format
    match = re.match(r'data:([^;]+);base64,(.+)', data)
    if not match:
        raise ValueError("Invalid base64 data URL format. Expected: 'data:image/<type>;base64,<data>'")

    mime_type = match.group(1)
    base64_data = match.group(2)

    try:
        image_bytes = base64.b64decode(base64_data)
        return image_bytes, mime_type
    except Exception as e:
        raise ValueError(f"Failed to decode base64 data: {e}")


def save_temp_image(image_bytes: bytes, extension: str = ".jpg") -> str:
    """
    Save image bytes to a temporary file.

    Args:
        image_bytes: Image data as bytes
        extension: File extension (default: .jpg)

    Returns:
        Path to the temporary file
    """
    fd, path = tempfile.mkstemp(suffix=extension)
    with open(fd, 'wb') as f:
        f.write(image_bytes)
    return path


def get_file_extension(mime_type: str) -> str:
    """
    Get file extension from MIME type.

    Args:
        mime_type: MIME type string (e.g., "image/jpeg")

    Returns:
        File extension including dot (e.g., ".jpg")
    """
    mime_to_ext = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/webp": ".webp",
    }
    return mime_to_ext.get(mime_type.lower(), ".jpg")


def cleanup_temp_file(path: str) -> None:
    """
    Clean up a temporary file.

    Args:
        path: Path to the temporary file
    """
    try:
        Path(path).unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {path}: {e}")
