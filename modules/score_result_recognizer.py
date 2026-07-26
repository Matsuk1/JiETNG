"""
maimai result-photo OCR integration.

This module wraps the standalone scripts under scripts/ so main.py can call the
recognizer without importing CLI code directly.
"""
from __future__ import annotations

import logging
import sys
import threading
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image
from PIL import UnidentifiedImageError


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


_ENGINE: Any | None = None
_ENGINE_LOCK = threading.Lock()
_OCR_LOCK = threading.Lock()
_OCR_FIELDS: tuple[str, ...] | None = None
_PROCESS_IMAGE_DATA: Any | None = None
SUPPORTED_SCORE_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_SCORE_IMAGE_PIXELS = 40_000_000


class InvalidScoreImageError(ValueError):
    """The uploaded data is not a supported, safely sized score image."""


class UnsupportedScoreImageError(InvalidScoreImageError):
    """The uploaded image format is not supported by the OCR API."""


def _load_ocr_module() -> tuple[tuple[str, ...], Any, Any]:
    global _OCR_FIELDS, _PROCESS_IMAGE_DATA
    if _OCR_FIELDS is None or _PROCESS_IMAGE_DATA is None:
        from score_result_ocr import OCR_FIELDS, PaddleOcrEngine, process_image_data

        _OCR_FIELDS = OCR_FIELDS
        _PROCESS_IMAGE_DATA = process_image_data
        return OCR_FIELDS, PaddleOcrEngine, process_image_data

    from score_result_ocr import PaddleOcrEngine

    return _OCR_FIELDS, PaddleOcrEngine, _PROCESS_IMAGE_DATA


def _engine() -> Any:
    global _ENGINE
    with _ENGINE_LOCK:
        if _ENGINE is None:
            _, PaddleOcrEngine, _ = _load_ocr_module()
            _ENGINE = PaddleOcrEngine(lang="japan")
        return _ENGINE


def initialize_score_recognizer() -> None:
    _engine()


def recognize_score_image_bytes(
    image_bytes: bytes,
    fields: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            image_format = str(source.format or "").upper()
            if image_format not in SUPPORTED_SCORE_IMAGE_FORMATS:
                raise UnsupportedScoreImageError(
                    "Supported image formats are JPEG, PNG, and WebP"
                )
            width, height = source.size
            if width <= 0 or height <= 0 or width * height > MAX_SCORE_IMAGE_PIXELS:
                raise InvalidScoreImageError(
                    f"Image dimensions exceed the {MAX_SCORE_IMAGE_PIXELS}-pixel limit"
                )
            image = source.convert("RGB")
    except UnsupportedScoreImageError:
        raise
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidScoreImageError("Uploaded data is not a valid image") from exc

    # PaddleOCR inference is heavy and may not be thread-safe across concurrent
    # LINE tasks. Serialize access to the shared model instance.
    lock_started_at = time.perf_counter()
    with _OCR_LOCK:
        lock_wait_seconds = time.perf_counter() - lock_started_at
        if lock_wait_seconds >= 0.01:
            logger.info("Score OCR lock wait: %.3fs", lock_wait_seconds)
        ocr_fields, _, process_image_data = _load_ocr_module()
        return process_image_data(
            image,
            fields or ocr_fields,
            _engine(),
        )
