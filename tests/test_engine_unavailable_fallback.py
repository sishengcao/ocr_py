"""
Tests for engine unavailable fallback scenario.

When the requested engine is not available (not configured),
the system should fallback to the default engine and mark fallback_used = true.
"""

import pytest
from unittest.mock import MagicMock
from app.core.engine_router import EngineRouter, get_engine_router
from app.engines.base import OcrOptions, OcrResult, OcrEngine


class MockPaddleOcrEngine(OcrEngine):
    """Mock PaddleOCR engine for testing."""

    def __init__(self):
        super().__init__("paddleocr")
        self._available = True

    def is_available(self):
        return self._available

    def set_available(self, available):
        self._available = available

    def recognize(self, image_path: str, options: OcrOptions) -> OcrResult:
        return OcrResult(
            success=True,
            text="Mock OCR result",
            lines=[],
            elapsed_time=0.5,
            engine=self.name
        )

    def get_status(self):
        return {
            "engine": "PaddleOCR",
            "name": self.name,
            "available": self._available,
            "version": "3.4.0",
            "supported_languages": ["ch", "en"]
        }

    def get_supported_languages(self):
        return ["ch", "en"]


class TestEngineUnavailableFallback:
    """Tests for when requested engine is unavailable."""

    def test_unavailable_engine_fallback_marks_fallback_used_true(self):
        """When requested engine is unavailable, fallback_used should be true."""
        from app.engines.factory import EngineFactory

        # Clear engines
        EngineFactory._engines.clear()

        # Only register paddleocr
        paddle_engine = MockPaddleOcrEngine()
        EngineFactory.register(paddle_engine)

        router = get_engine_router()
        router.set_default_engine("paddleocr")

        # Request an engine which is not available
        result = router.recognize(
            "/fake/path.jpg",
            OcrOptions(lang="ch"),
            engine_name="unavailable_engine",
            enable_fallback=True
        )

        # Even if recognition succeeds, fallback_used should be true
        # because we had to switch from unavailable_engine to paddleocr
        assert result.requested_engine == "unavailable_engine"
        assert result.engine == "paddleocr"
        assert result.fallback_used is True, "fallback_used should be true when requested engine is unavailable"

    def test_unavailable_engine_without_fallback_returns_error(self):
        """When requested engine is unavailable and fallback disabled, should return error."""
        from app.engines.factory import EngineFactory

        # Clear engines
        EngineFactory._engines.clear()

        # Only register paddleocr
        paddle_engine = MockPaddleOcrEngine()
        EngineFactory.register(paddle_engine)

        router = get_engine_router()

        # Request unavailable engine with fallback disabled
        result = router.recognize(
            "/fake/path.jpg",
            OcrOptions(lang="ch"),
            engine_name="unavailable_engine",
            enable_fallback=False
        )

        # Should fail with no available engine
        assert result.success is False
        assert result.requested_engine == "unavailable_engine"
        assert result.fallback_used is False

    def test_available_engine_no_fallback(self):
        """When requested engine is available, no fallback should occur."""
        from app.engines.factory import EngineFactory

        # Clear engines
        EngineFactory._engines.clear()

        # Register both engines
        paddle_engine = MockPaddleOcrEngine()
        EngineFactory.register(paddle_engine)

        router = get_engine_router()
        router.set_default_engine("paddleocr")

        # Request paddleocr which is available
        result = router.recognize(
            "/fake/path.jpg",
            OcrOptions(lang="ch"),
            engine_name="paddleocr",
            enable_fallback=True
        )

        # No fallback should occur
        assert result.requested_engine == "paddleocr"
        assert result.engine == "paddleocr"
        assert result.fallback_used is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
