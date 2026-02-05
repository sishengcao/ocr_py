"""
Tests for engine fallback metadata tracking.

These tests verify that when fallback occurs, the response correctly
reports the requested engine, actual engine, and whether fallback was used.
"""

import pytest
from app.core.engine_router import EngineRouter, get_engine_router
from app.engines.base import OcrOptions, OcrResult
from app.engines.paddleocr_engine import PaddleOcrEngine


class MockEngine:
    """Mock OCR engine for testing."""

    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self._should_fail = should_fail

    def is_available(self) -> bool:
        return True

    def recognize(self, image_path: str, options: OcrOptions) -> OcrResult:
        if self._should_fail:
            return OcrResult(
                success=False,
                text="",
                lines=[],
                elapsed_time=0.1,
                error=f"{self.name} failed",
                engine=self.name
            )
        return OcrResult(
            success=True,
            text="Mock text",
            lines=[{"text": "Mock text", "box": [[0, 0], [1, 0], [1, 1], [0, 1]], "confidence": 1.0}],
            elapsed_time=0.5,
            engine=self.name
        )

    def get_status(self):
        return {"engine": self.name, "available": True}

    def get_supported_languages(self):
        return ["ch", "en"]


class TestEngineFallbackMetadata:
    """Tests for fallback metadata tracking."""

    def setup_method(self):
        """Clean up engine factory before each test."""
        from app.engines.factory import EngineFactory
        # Clear all registered engines
        EngineFactory._engines.clear()

    def test_requested_engine_recorded_when_no_fallback(self):
        """When engine succeeds, requested_engine should match engine."""
        from app.engines.factory import EngineFactory

        # Register mock engine
        mock_engine = MockEngine("test_engine", should_fail=False)
        EngineFactory.register(mock_engine)

        router = get_engine_router()
        result = router.recognize(
            "/fake/path.jpg",
            OcrOptions(lang="ch"),
            engine_name="test_engine",
            enable_fallback=False
        )

        assert result.success is True
        assert result.engine == "test_engine"
        assert result.requested_engine == "test_engine"
        assert result.fallback_used is False

    def test_fallback_metadata_set_when_fallback_occurs(self):
        """When fallback occurs, metadata should reflect the original request."""
        from app.engines.factory import EngineFactory

        # Register failing engine
        failing_engine = MockEngine("failing_engine", should_fail=True)
        EngineFactory.register(failing_engine)

        # Register working fallback engine
        fallback_engine = MockEngine("fallback_engine", should_fail=False)
        EngineFactory.register(fallback_engine)

        router = get_engine_router()
        result = router.recognize(
            "/fake/path.jpg",
            OcrOptions(lang="ch"),
            engine_name="failing_engine",
            enable_fallback=True
        )

        # Should succeed with fallback
        assert result.success is True
        # Actual engine that performed recognition
        assert result.engine == "fallback_engine"
        # Original engine requested by user
        assert result.requested_engine == "failing_engine"
        # Fallback was used
        assert result.fallback_used is True

    def test_fallback_used_false_when_engine_succeeds(self):
        """When primary engine succeeds, fallback_used should be False."""
        from app.engines.factory import EngineFactory

        working_engine = MockEngine("working_engine", should_fail=False)
        EngineFactory.register(working_engine)

        router = get_engine_router()
        result = router.recognize(
            "/fake/path.jpg",
            OcrOptions(lang="ch"),
            engine_name="working_engine",
            enable_fallback=True
        )

        assert result.success is True
        assert result.engine == "working_engine"
        assert result.requested_engine == "working_engine"
        assert result.fallback_used is False

    def test_requested_engine_none_for_default_engine(self):
        """When no engine specified, requested_engine should be None."""
        from app.engines.factory import EngineFactory

        mock_engine = MockEngine("mock_default", should_fail=False)
        EngineFactory.register(mock_engine)

        router = get_engine_router()
        router.set_default_engine("mock_default")

        result = router.recognize(
            "/fake/path.jpg",
            OcrOptions(lang="ch"),
            engine_name=None,
            enable_fallback=False
        )

        assert result.success is True
        assert result.engine == "mock_default"
        assert result.requested_engine is None
        assert result.fallback_used is False

    def test_all_engines_fail_returns_error_with_metadata(self):
        """When all engines fail, metadata should still be set correctly."""
        from app.engines.factory import EngineFactory

        # Register two failing engines
        failing1 = MockEngine("failing1", should_fail=True)
        failing2 = MockEngine("failing2", should_fail=True)
        EngineFactory.register(failing1)
        EngineFactory.register(failing2)

        router = get_engine_router()
        result = router.recognize(
            "/fake/path.jpg",
            OcrOptions(lang="ch"),
            engine_name="failing1",
            enable_fallback=True
        )

        # Should fail
        assert result.success is False
        assert result.requested_engine == "failing1"
        assert result.fallback_used is False  # No successful fallback occurred

    def test_paddleocr_response_structure(self):
        """Verify PaddleOCR response has correct structure."""
        paddle_engine = PaddleOcrEngine()
        if not paddle_engine.is_available():
            pytest.skip("PaddleOCR not available")

        # Test with a real minimal image
        import tempfile
        import base64

        # Create a minimal test PNG
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(png_data)
            temp_path = f.name

        try:
            result = paddle_engine.recognize(temp_path, OcrOptions(lang="ch"))

            # Check structure
            assert isinstance(result.text, str)
            assert isinstance(result.lines, list)
            assert isinstance(result.elapsed_time, float)
            assert result.engine == "paddleocr"
            assert result.requested_engine is None  # Direct call, not through router
            assert result.fallback_used is False
        finally:
            import os
            os.unlink(temp_path)


    def test_ocro_result_structure(self):
        """Verify OcrResult has correct structure."""
        # Test the structure
        result = OcrResult(
            success=True,
            text="Test text",
            lines=[{"text": "Test", "box": [[0, 0], [1, 0], [1, 1], [0, 1]], "confidence": 0.95}],
            elapsed_time=1.5,
            engine="test_engine",
            requested_engine="test_engine",
            fallback_used=False
        )

        assert result.success is True
        assert result.engine == "test_engine"
        assert result.requested_engine == "test_engine"
        assert result.fallback_used is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
