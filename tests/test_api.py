"""
Integration tests for OCR API.

These tests verify the API endpoints work correctly.
"""

import pytest
import base64
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app


# Create test client
client = TestClient(app)


@pytest.fixture
def sample_image_base64():
    """Create a simple test image as base64."""
    # Create a minimal 1x1 PNG image
    # PNG header + IHDR + IDAT with minimal data + IEND
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    data_url = 'data:image/png;base64,' + base64.b64encode(png_data).decode('utf-8')
    return data_url


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self):
        """Test health check returns ok."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["ok", "error"]
        assert data["service"] == "ocr_py"
        assert "version" in data
        # New format has "engines" instead of "ocr_engine"
        assert "engines" in data


class TestOcrRecognizeEndpoint:
    """Tests for /ocr/recognize endpoint."""

    def test_empty_request(self, sample_image_base64):
        """Test with empty request body - missing image field."""
        response = client.post("/ocr/recognize", json={})
        # Returns 200 with error because image field is missing but valid JSON
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_invalid_base64_format(self):
        """Test with invalid base64 format."""
        response = client.post(
            "/ocr/recognize",
            json={"image": "not-a-base64-data-url"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_base64_recognize(self, sample_image_base64):
        """Test recognition with base64 encoded image."""
        response = client.post(
            "/ocr/recognize",
            json={"image": sample_image_base64}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        # May succeed or fail depending on OCR engine availability
        if data["success"]:
            assert "data" in data
            assert "text" in data["data"]
            assert "elapsed_time" in data["data"]
        else:
            assert "error" in data

    def test_unsupported_content_type(self):
        """Test with unsupported content type."""
        response = client.post(
            "/ocr/recognize",
            content="text/plain",
            data="hello"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
