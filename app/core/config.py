"""
Configuration management for OCR service.

This module handles environment-based configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8808"))

    # OCR
    OCR_LANG: str = os.getenv("OCR_LANG", "ch")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Upload
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", str(50 * 1024 * 1024)))

    # Service info
    SERVICE_NAME: str = "ocr_py"
    VERSION: str = "1.0.0"


# Global config instance
config = Config()
