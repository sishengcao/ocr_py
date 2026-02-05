"""
OCR Engine Factory

This module provides a factory for creating and managing OCR engine instances.
"""

import logging
from typing import Dict, Optional

from app.engines.base import OcrEngine


logger = logging.getLogger(__name__)


class EngineFactory:
    """
    Factory for managing OCR engine instances.

    This class provides singleton access to registered OCR engines
    and handles engine lifecycle.
    """

    _engines: Dict[str, OcrEngine] = {}

    @classmethod
    def register(cls, engine: OcrEngine) -> None:
        """
        Register an OCR engine.

        Args:
            engine: The engine instance to register
        """
        cls._engines[engine.name] = engine
        logger.info(f"Registered OCR engine: {engine.name}")

    @classmethod
    def get(cls, name: str) -> Optional[OcrEngine]:
        """
        Get a registered OCR engine by name.

        Args:
            name: The engine name

        Returns:
            The engine instance, or None if not found
        """
        return cls._engines.get(name)

    @classmethod
    def get_all(cls) -> Dict[str, OcrEngine]:
        """
        Get all registered engines.

        Returns:
            Dictionary of engine name to engine instance
        """
        return cls._engines.copy()

    @classmethod
    def get_available(cls) -> Dict[str, OcrEngine]:
        """
        Get all available (ready) engines.

        Returns:
            Dictionary of available engines
        """
        return {
            name: engine
            for name, engine in cls._engines.items()
            if engine.is_available()
        }

    @classmethod
    def get_default(cls) -> Optional[OcrEngine]:
        """
        Get the default OCR engine.

        Returns the first available engine, preferring PaddleOCR.

        Returns:
            The default engine, or None if no engines available
        """
        available = cls.get_available()
        # Prefer PaddleOCR as default
        if "paddleocr" in available:
            return available["paddleocr"]
        if available:
            return next(iter(available.values()))
        return None
