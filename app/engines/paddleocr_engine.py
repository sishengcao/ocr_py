"""
PaddleOCR Engine Implementation

This module implements the PaddleOCR adapter as an OCR engine.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional

# Set oneDNN compatibility environment variables BEFORE importing PaddleOCR
os.environ['USE_ONEDNN'] = '0'
os.environ['MKL_THREADING_LAYER'] = 'GNU'

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

from app.engines.base import OcrEngine, OcrOptions, OcrResult


logger = logging.getLogger(__name__)


class PaddleOcrEngine(OcrEngine):
    """
    PaddleOCR engine implementation.

    This engine uses PaddleOCR for text recognition with support for
    multiple languages including simplified and traditional Chinese.
    """

    # Supported languages
    SUPPORTED_LANGUAGES = {
        "ch": "Chinese (Simplified)",
        "ch_traditional": "Chinese (Traditional)",
        "en": "English",
        "fr": "French",
        "german": "German",
        "korean": "Korean",
        "japan": "Japanese",
    }

    def __init__(self):
        """Initialize the PaddleOCR engine."""
        super().__init__("paddleocr")
        self._engine: Optional[Any] = None
        self._initialized = False

        if PADDLEOCR_AVAILABLE:
            self._initialize()
        else:
            logger.warning("PaddleOCR is not available")

    def _initialize(self) -> None:
        """Initialize the PaddleOCR engine."""
        if self._initialized:
            return

        try:
            # Initialize with default Chinese support
            # Note: show_log parameter removed in PaddleOCR 3.x
            self._engine = PaddleOCR(
                lang='ch',
                use_angle_cls=True
            )
            self._initialized = True
            logger.info("PaddleOCR engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self._engine = None
            self._initialized = True

    def recognize(self, image_path: str, options: OcrOptions) -> OcrResult:
        """
        Recognize text from an image file.

        Args:
            image_path: Path to the image file
            options: OCR recognition options

        Returns:
            OcrResult containing the recognition results
        """
        start_time = time.monotonic()

        if not self.is_available():
            return OcrResult(
                success=False,
                text="",
                lines=[],
                elapsed_time=0.0,
                error="PaddleOCR engine not available",
                engine=self.name
            )

        try:
            from pathlib import Path
            path = Path(image_path)
            if not path.exists():
                return OcrResult(
                    success=False,
                    text="",
                    lines=[],
                    elapsed_time=0.0,
                    error=f"Image file not found: {image_path}",
                    engine=self.name
                )

            # Run OCR
            result = self._engine.ocr(str(image_path))

            # Parse results
            text_lines, structured_lines = self._parse_ocr_result(result)

            elapsed_time = time.monotonic() - start_time

            return OcrResult(
                success=True,
                text="\n".join(text_lines),
                lines=structured_lines,
                elapsed_time=elapsed_time,
                engine=self.name
            )

        except Exception as e:
            logger.error(f"PaddleOCR processing failed: {e}")
            return OcrResult(
                success=False,
                text="",
                lines=[],
                elapsed_time=max(0.0, time.monotonic() - start_time),
                error=str(e),
                engine=self.name
            )

    def _parse_ocr_result(self, result: Any) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        Parse PaddleOCR result into text lines and structured data.

        Args:
            result: Raw result from PaddleOCR

        Returns:
            Tuple of (text_lines, structured_lines)
        """
        text_lines: List[str] = []
        structured_lines: List[Dict[str, Any]] = []

        if not result:
            return text_lines, structured_lines

        # PaddleOCR 3.x format - dictionary based
        if isinstance(result, list) and len(result) > 0:
            first_item = result[0]

            # Check if this is PaddleOCR 3.x format (dictionary)
            if isinstance(first_item, dict):
                rec_texts = first_item.get('rec_texts', [])
                rec_scores = first_item.get('rec_scores', [])
                rec_polys = first_item.get('rec_polys', [])

                for i, text in enumerate(rec_texts):
                    confidence = float(rec_scores[i]) if i < len(rec_scores) else 1.0

                    # Convert numpy array to list for JSON serialization
                    box = rec_polys[i].tolist() if i < len(rec_polys) else []

                    text_lines.append(text)
                    structured_lines.append({
                        "text": text,
                        "box": box,
                        "confidence": confidence
                    })

                logger.info(f"Extracted {len(text_lines)} text lines from PaddleOCR 3.x")
                return text_lines, structured_lines

            # PaddleOCR 2.6+ format (legacy list format)
            lines_to_process = []

            if first_item:
                if len(first_item) > 0 and isinstance(first_item[0], list):
                    if (len(first_item[0]) == 4 and
                        all(isinstance(coord, (int, float)) for coord in first_item[0][0]) if first_item[0] else False):
                        lines_to_process = [first_item]
                    else:
                        lines_to_process = first_item
                else:
                    lines_to_process = [first_item]

            for line in lines_to_process:
                if not isinstance(line, (list, tuple)) or len(line) < 2:
                    continue

                box = line[0]
                text = None
                confidence = 1.0

                second_item = line[1]
                if isinstance(second_item, (list, tuple)) and len(second_item) >= 2:
                    text = second_item[0]
                    confidence = float(second_item[1])
                elif isinstance(second_item, str):
                    text = second_item

                if text is not None:
                    text_lines.append(text)
                    structured_lines.append({
                        "text": text,
                        "box": box,
                        "confidence": confidence
                    })

            logger.info(f"Extracted {len(text_lines)} text lines from PaddleOCR 2.x")
        else:
            logger.warning(f"Unexpected PaddleOCR result format: {type(result)}")

        return text_lines, structured_lines

    def get_status(self) -> Dict[str, Any]:
        """
        Get the engine status and capabilities.

        Returns:
            Dictionary with engine status information
        """
        # Try to get actual version
        version = "3.3.0"
        try:
            import paddleocr
            version = getattr(paddleocr, '__version__', '3.3.0')
        except:
            pass

        return {
            "engine": "PaddleOCR",
            "name": self.name,
            "available": PADDLEOCR_AVAILABLE and self._engine is not None,
            "version": version,
            "supported_languages": list(self.SUPPORTED_LANGUAGES.keys()),
        }

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of language codes supported by this engine
        """
        return list(self.SUPPORTED_LANGUAGES.keys())
