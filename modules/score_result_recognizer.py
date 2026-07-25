"""
maimai result-photo OCR integration.

This module wraps the standalone scripts under scripts/ so main.py can call the
recognizer without importing CLI code directly.
"""
from __future__ import annotations

import sys
import threading
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


_ENGINES: dict[str, Any] = {}
_ENGINE_LOCK = threading.Lock()
_OCR_LOCK = threading.Lock()
_OCR_FIELDS: tuple[str, ...] | None = None
_PROCESS_IMAGE_DATA: Any | None = None


def _load_ocr_module() -> tuple[tuple[str, ...], Any, Any]:
    global _OCR_FIELDS, _PROCESS_IMAGE_DATA
    if _OCR_FIELDS is None or _PROCESS_IMAGE_DATA is None:
        from score_result_ocr import OCR_FIELDS, PaddleOcrEngine, process_image_data

        _OCR_FIELDS = OCR_FIELDS
        _PROCESS_IMAGE_DATA = process_image_data
        return OCR_FIELDS, PaddleOcrEngine, process_image_data

    from score_result_ocr import PaddleOcrEngine

    return _OCR_FIELDS, PaddleOcrEngine, _PROCESS_IMAGE_DATA


def _engine(model_profile: str = "small") -> Any:
    profile = model_profile.lower()
    if profile not in {"medium", "small"}:
        raise ValueError(f"unsupported score OCR model profile: {model_profile}")
    with _ENGINE_LOCK:
        if profile not in _ENGINES:
            _, PaddleOcrEngine, _ = _load_ocr_module()
            _ENGINES[profile] = PaddleOcrEngine(lang="japan", model_profile=profile)
        return _ENGINES[profile]


def initialize_score_recognizer() -> None:
    _engine("small")


def recognize_score_image_bytes(
    image_bytes: bytes,
    fields: tuple[str, ...] | None = None,
    model_profile: str = "small",
) -> dict[str, Any]:
    with Image.open(BytesIO(image_bytes)) as source:
        image = source.copy()

    # PaddleOCR inference is heavy and may not be thread-safe across concurrent
    # LINE tasks. Serialize access to the shared model instance.
    with _OCR_LOCK:
        ocr_fields, _, process_image_data = _load_ocr_module()
        result = process_image_data(
            image,
            fields or ocr_fields,
            _engine(model_profile),
        )
        result["ocr_model_profile"] = model_profile.lower()
        return result
