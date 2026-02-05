"""
OCR Engine Router

This module provides routing logic for OCR engine selection and fallback.
"""

import logging
from typing import Optional

from app.engines.base import OcrEngine, OcrOptions, OcrResult
from app.engines.factory import EngineFactory


logger = logging.getLogger(__name__)


class EngineRouter:
    """
    Router for OCR engine selection.

    This class handles engine selection based on user preference
    and provides automatic fallback if the preferred engine fails.
    """

    def __init__(self):
        """Initialize the engine router."""
        self._default_engine: Optional[str] = "paddleocr"

    def get_engine(self, engine_name: Optional[str] = None) -> Optional[OcrEngine]:
        """
        Get an OCR engine by name.

        Args:
            engine_name: The requested engine name, or None for default

        Returns:
            The engine instance, or None if not found/unavailable
        """
        # Use default if no specific engine requested
        if engine_name is None:
            engine_name = self._default_engine

        # Try to get the requested engine
        engine = EngineFactory.get(engine_name)

        if engine is None:
            logger.warning(f"Engine '{engine_name}' not found")
            return None

        if not engine.is_available():
            logger.warning(f"Engine '{engine_name}' is not available")
            return None

        return engine

    def recognize(
        self,
        image_path: str,
        options: OcrOptions,
        engine_name: Optional[str] = None,
        enable_fallback: bool = True
    ) -> OcrResult:
        """
        Recognize text using the specified engine.

        Args:
            image_path: Path to the image file
            options: OCR recognition options
            engine_name: The requested engine name
            enable_fallback: Whether to try fallback engines on failure

        Returns:
            OcrResult containing the recognition results
        """
        # Store the originally requested engine
        requested_engine = engine_name

        # Track if we need to mark fallback due to unavailability
        fallback_needed = False

        # Get the requested engine
        engine = self.get_engine(engine_name)

        if engine is None:
            # Try default engine as fallback
            if enable_fallback and engine_name != self._default_engine:
                logger.info(f"Requested engine '{engine_name}' not available, trying default: {self._default_engine}")
                engine = self.get_engine(self._default_engine)
                if engine is not None:
                    fallback_needed = True

        if engine is None:
            return OcrResult(
                success=False,
                text="",
                lines=[],
                elapsed_time=0.0,
                error=f"No available OCR engine (requested: {engine_name})",
                engine="none",
                requested_engine=requested_engine,
                fallback_used=False
            )

        # Perform recognition with the primary engine
        result = engine.recognize(image_path, options)

        # Set metadata for the result
        result.requested_engine = requested_engine
        result.fallback_used = fallback_needed

        # If failed and fallback is enabled, try other engines
        if not result.success and enable_fallback:
            available_engines = EngineFactory.get_available()
            for fallback_name, fallback_engine in available_engines.items():
                if fallback_name != engine.name:
                    logger.info(f"Primary engine '{engine.name}' failed, trying fallback: {fallback_name}")
                    fallback_result = fallback_engine.recognize(image_path, options)
                    if fallback_result.success:
                        # Set metadata to indicate fallback was used
                        fallback_result.requested_engine = requested_engine
                        fallback_result.fallback_used = True
                        logger.info(f"Using fallback engine '{fallback_name}' (requested: '{requested_engine}', actual: '{fallback_name}')")
                        return fallback_result

        return result

    def list_engines(self) -> dict:
        """
        List all available engines with their status.

        Returns:
            Dictionary of engine information
        """
        engines = EngineFactory.get_all()
        return {
            name: {
                "available": engine.is_available(),
                "status": engine.get_status()
            }
            for name, engine in engines.items()
        }

    def get_default_engine(self) -> str:
        """
        Get the default engine name.

        Returns:
            The default engine name
        """
        return self._default_engine

    def set_default_engine(self, engine_name: str) -> bool:
        """
        Set the default engine.

        Args:
            engine_name: The engine name to set as default

        Returns:
            True if the default was changed successfully
        """
        if EngineFactory.get(engine_name) is not None:
            self._default_engine = engine_name
            logger.info(f"Default engine set to: {engine_name}")
            return True
        return False


# Global router instance
_engine_router: Optional[EngineRouter] = None


def get_engine_router() -> EngineRouter:
    """
    Get the global engine router instance.

    Returns:
        The EngineRouter instance
    """
    global _engine_router
    if _engine_router is None:
        _engine_router = EngineRouter()
    return _engine_router
