"""
OCR Engine Base Class

This module defines the abstract base class for all OCR engines.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class OcrOptions:
    """
    OCR recognition options.

    Attributes:
        lang: Language code (ch, en, ch_traditional, etc.)
        enable_table: Enable table recognition
        enable_formula: Enable formula recognition
        return_details: Return detailed line information
    """
    lang: str = "ch"
    enable_table: bool = False
    enable_formula: bool = False
    return_details: bool = True

    def __post_init__(self):
        """Normalize language codes."""
        # Map common language aliases
        lang_map = {
            "zh": "ch",
            "zh-cn": "ch",
            "zh-tw": "ch_traditional",
            "zh-hk": "ch_traditional",
            "traditional": "ch_traditional",
            "simplified": "ch",
        }
        if self.lang in lang_map:
            self.lang = lang_map[self.lang]


@dataclass
class OcrResult:
    """
    OCR recognition result.

    Attributes:
        success: Whether recognition was successful
        text: Full recognized text
        lines: Individual text lines with details
        elapsed_time: Processing time in seconds
        error: Error message if failed
        engine: Engine name that produced the result
        requested_engine: Engine name requested by user (may differ from engine if fallback occurred)
        fallback_used: Whether a fallback engine was used
    """
    success: bool
    text: str
    lines: List[Dict[str, Any]]
    elapsed_time: float
    error: Optional[str] = None
    engine: str = "unknown"
    requested_engine: Optional[str] = None
    fallback_used: bool = False


class OcrEngine(ABC):
    """
    Abstract base class for OCR engines.

    All OCR engines must inherit from this class and implement
    the recognize method.
    """

    def __init__(self, name: str):
        """
        Initialize the OCR engine.

        Args:
            name: Engine identifier name
        """
        self._name = name

    @property
    def name(self) -> str:
        """Get the engine name."""
        return self._name

    @abstractmethod
    def recognize(self, image_path: str, options: OcrOptions) -> OcrResult:
        """
        Recognize text from an image file.

        Args:
            image_path: Path to the image file
            options: OCR recognition options

        Returns:
            OcrResult containing the recognition results
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the engine status and capabilities.

        Returns:
            Dictionary with engine status information
        """
        pass

    def is_available(self) -> bool:
        """
        Check if the engine is available and ready.

        Returns:
            True if the engine can process requests
        """
        status = self.get_status()
        return status.get("available", False)

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of language codes supported by this engine
        """
        return ["ch", "en", "ch_traditional"]
