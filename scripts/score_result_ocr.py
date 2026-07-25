#!/usr/bin/env python3
"""OCR pipeline and command-line debugger for maimai result photos."""
from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from score_result_cropper import crop_result_fields, crop_result_fields_in_memory, iter_images


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(PROJECT_ROOT / ".paddle-home" / "paddlex"))
os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "huggingface")
os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "0")
os.environ.setdefault("FLAGS_use_onednn", "0")
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_enable_pir_api", "0")

OCR_FIELDS = (
    "main_title",
    "main_achievement",
    "sub_judgement_table",
)

OCR_MODEL_PROFILES = {
    "tiny": ("PP-OCRv6_tiny_det", "PP-OCRv6_tiny_rec"),
    "small": ("PP-OCRv6_small_det", "PP-OCRv6_small_rec"),
    "balanced": ("PP-OCRv6_small_det", "PP-OCRv6_medium_rec"),
    "medium": ("PP-OCRv6_medium_det", "PP-OCRv6_medium_rec"),
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    replacements = {
        "％": "%",
        "／": "/",
        "｜": "/",
        "|": "/",
        "﹣": "-",
        "−": "-",
        "ー": "-",
        "Ｏ": "0",
        "O": "0",
        "o": "0",
        "I": "1",
        "l": "1",
    }
    for before, after in replacements.items():
        value = value.replace(before, after)
    return re.sub(r"\s+", " ", value).strip()


def normalize_song_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    # The title crop can still include UI labels from the same header band.
    value = re.sub(r"(NEW\s*RECORD|MY\s*BEST|ACHIEVEMENT|TRACK\s*\d+)", " ", value, flags=re.IGNORECASE)
    value = re.sub(
        r"(RE\s*[:\-]?\s*MASTER|MASTER|EXPERT|ADVANCED|BASIC|LV\s*\d+\+?)",
        " ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"(でらっくす|てらっくす|DX)", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip()
    return value.strip(" -|")


def prepare_ocr_image_data(source_image: Image.Image, field: str) -> Image.Image:
    image = ImageOps.exif_transpose(source_image).convert("RGB")
    scale = 3 if field in {"sub_judgement_table", "sub_judgement_column"} else 2
    image = image.resize((image.width * scale, image.height * scale), Image.Resampling.LANCZOS)

    if field == "sub_judgement_column":
        image = ImageOps.autocontrast(image, cutoff=1)
        image = ImageEnhance.Contrast(image).enhance(1.75)
        image = ImageEnhance.Sharpness(image).enhance(2.0)
    elif field in {"main_achievement", "rating", "dx_score", "max_combo", "judgement", "level"}:
        image = ImageEnhance.Contrast(image).enhance(1.65)
        image = ImageEnhance.Sharpness(image).enhance(1.75)
    else:
        image = ImageEnhance.Contrast(image).enhance(1.35)
        image = ImageEnhance.Sharpness(image).enhance(1.45)

    image = image.filter(ImageFilter.SHARPEN)
    return image


def prepare_ocr_image(source_path: str | Path, output_path: str | Path, field: str) -> Path:
    image = prepare_ocr_image_data(Image.open(source_path), field)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output


class PaddleOcrEngine:
    def __init__(self, lang: str = "japan", model_profile: str | None = None) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed. Install it in the test environment with: "
                "python3 -m pip install paddlepaddle paddleocr"
            ) from exc

        profile = (model_profile or os.getenv("SCORE_OCR_MODEL_PROFILE", "small")).lower()
        if profile not in OCR_MODEL_PROFILES:
            supported = ", ".join(OCR_MODEL_PROFILES)
            raise RuntimeError(
                f"unsupported SCORE_OCR_MODEL_PROFILE={profile!r}; expected one of: {supported}"
            )
        detection_model, recognition_model = OCR_MODEL_PROFILES[profile]
        model_kwargs = {
            "text_detection_model_name": detection_model,
            "text_recognition_model_name": recognition_model,
        }
        self.model_profile = profile
        self.model_names = (detection_model, recognition_model)

        init_attempts = (
            {
                **model_kwargs,
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": False,
                "enable_mkldnn": False,
                "cpu_threads": 4,
            },
            {**model_kwargs, "use_textline_orientation": False, "enable_mkldnn": False},
            {**model_kwargs, "use_angle_cls": False, "show_log": False, "enable_mkldnn": False},
            model_kwargs,
        )
        last_error: Exception | None = None
        for kwargs in init_attempts:
            try:
                self.ocr = PaddleOCR(**kwargs)
                break
            except Exception as exc:  # pragma: no cover - depends on PaddleOCR version
                last_error = exc
        else:
            raise RuntimeError(f"failed to initialize PaddleOCR: {last_error}") from last_error

    def read(self, image_source: str | Path | Image.Image) -> list[dict[str, Any]]:
        if isinstance(image_source, Image.Image):
            import numpy as np

            source = np.asarray(image_source.convert("RGB"))
        else:
            source = str(image_source)
        attempts = [
            ("predict", lambda: self.ocr.predict(source)),
            ("ocr", lambda: self.ocr.ocr(source)),
        ]

        try:
            ocr_parameters = inspect.signature(self.ocr.ocr).parameters
        except (TypeError, ValueError):
            ocr_parameters = {}
        if "cls" in ocr_parameters:
            attempts.append(("ocr(cls=False)", lambda: self.ocr.ocr(source, cls=False)))

        errors: list[str] = []
        for name, attempt in attempts:
            try:
                return extract_ocr_items(attempt())
            except Exception as exc:  # pragma: no cover - depends on PaddleOCR version
                errors.append(f"{name}: {type(exc).__name__}: {exc}")
        source_name = str(image_source) if not isinstance(image_source, Image.Image) else "in-memory image"
        raise RuntimeError(f"OCR failed for {source_name}: {'; '.join(errors)}")


def extract_ocr_items(result: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if node is None:
            return
        if isinstance(node, dict):
            texts = node.get("rec_texts")
            scores = node.get("rec_scores")
            if scores is None:
                scores = []
            boxes = node.get("rec_boxes")
            if boxes is None:
                boxes = node.get("dt_polys")
            if boxes is None:
                boxes = []
            if isinstance(texts, list):
                for index, text in enumerate(texts):
                    items.append({
                        "text": str(text),
                        "score": float(scores[index]) if index < len(scores) else None,
                        "box": _jsonable_box(boxes[index]) if index < len(boxes) else None,
                    })
                return
            for value in node.values():
                walk(value)
            return
        if isinstance(node, (list, tuple)):
            if len(node) >= 2 and isinstance(node[1], (list, tuple)) and len(node[1]) >= 1 and isinstance(node[1][0], str):
                items.append({
                    "text": node[1][0],
                    "score": float(node[1][1]) if len(node[1]) > 1 and isinstance(node[1][1], (int, float)) else None,
                    "box": _jsonable_box(node[0]),
                })
                return
            for value in node:
                walk(value)
            return
        json_attr = getattr(node, "json", None)
        if isinstance(json_attr, dict):
            walk(json_attr)

    walk(result)
    return items


def _jsonable_box(value: Any) -> Any:
    try:
        if hasattr(value, "tolist"):
            return value.tolist()
        if isinstance(value, tuple):
            return list(value)
        return value
    except Exception:
        return None


def joined_text(items: list[dict[str, Any]]) -> str:
    return normalize_text(" ".join(str(item.get("text", "")) for item in items if item.get("text")))


def joined_song_text(items: list[dict[str, Any]]) -> str:
    text = " ".join(str(item.get("text", "")) for item in items if item.get("text"))
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


def item_bounds(item: dict[str, Any]) -> tuple[float, float, float, float] | None:
    box = item.get("box")
    if not isinstance(box, list) or not box:
        return None
    if len(box) == 4 and all(isinstance(value, (int, float)) for value in box):
        left, top, right, bottom = (float(value) for value in box)
        return left, top, right, bottom
    xs: list[float] = []
    ys: list[float] = []
    for point in box:
        if isinstance(point, list) and len(point) >= 2:
            xs.append(float(point[0]))
            ys.append(float(point[1]))
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def extract_song_title(items: list[dict[str, Any]]) -> str:
    fragments = []
    for item in items:
        text = normalize_song_text(str(item.get("text", "")))
        bounds = item_bounds(item)
        if not text or bounds is None:
            continue
        left, top, right, bottom = bounds
        height = max(1.0, bottom - top)
        fragments.append({
            "text": text,
            "left": left,
            "center_y": (top + bottom) / 2,
            "width": max(1.0, right - left),
            "height": height,
        })
    if not fragments:
        return normalize_song_text(joined_song_text(items))

    fragments.sort(key=lambda fragment: fragment["center_y"])
    lines: list[list[dict[str, Any]]] = []
    for fragment in fragments:
        matching_line = next((
            line for line in lines
            if abs(
                fragment["center_y"]
                - sum(item["center_y"] for item in line) / len(line)
            ) <= max(fragment["height"], max(item["height"] for item in line)) * 0.65
        ), None)
        if matching_line is None:
            lines.append([fragment])
        else:
            matching_line.append(fragment)

    candidates = []
    for line in lines:
        line.sort(key=lambda fragment: fragment["left"])
        text = normalize_song_text(" ".join(fragment["text"] for fragment in line))
        if not text:
            continue
        compact = re.sub(r"[^A-Za-z0-9]", "", text)
        numeric_only = bool(re.fullmatch(r"[A-Za-z]?\d+(?:[.,]\d+)?%?", text.replace(" ", "")))
        score = (
            max(fragment["height"] for fragment in line) * 4
            + sum(fragment["width"] for fragment in line) * 0.05
            + len(text) * 2
        )
        if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text):
            score += 80
        if numeric_only or compact.upper() in {"NEWRECORD", "MYBEST", "ACHIEVEMENT"}:
            score -= 500
        candidates.append((score, text))

    if not candidates:
        return normalize_song_text(joined_song_text(items))
    return max(candidates, key=lambda candidate: candidate[0])[1]


def parse_result(fields: dict[str, dict[str, Any]]) -> dict[str, Any]:
    raw = {name: joined_text(data.get("items", [])) for name, data in fields.items()}
    if "main_title" in fields:
        raw["main_title"] = extract_song_title(fields["main_title"].get("items", []))
    sub_judgement_field = fields.get("sub_judgement_table", {})
    sub_judgement_items = sub_judgement_field.get("items", [])
    parsed: dict[str, Any] = {
        "title": normalize_song_text(raw.get("main_title", "")),
        "achievement": parse_percent(raw.get("main_achievement", "")),
        "sub_judgement": (
            sub_judgement_field.get("column_values")
            or parse_sub_judgement_items(sub_judgement_items)
            or parse_sub_judgement(raw.get("sub_judgement_table", ""))
        ),
    }
    parsed["raw"] = raw
    return parsed


def parse_difficulty(text: str) -> str | None:
    match = re.search(r"(RE[:\s-]*MASTER|MASTER|EXPERT|ADVANCED|BASIC)", text, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).upper().replace(" ", "").replace("-", "")
    return "Re:MASTER" if value.startswith("RE") else value


def parse_level(text: str) -> str | None:
    match = re.search(r"(?:LV)?\s*(\d{1,2}\+?)", text, re.IGNORECASE)
    return match.group(1) if match else None


def parse_percent(text: str) -> float | None:
    candidates = re.findall(r"(\d{2,3}[.,]\d{3,4})\s*%?", text)
    if not candidates:
        return None
    try:
        return max(float(item.replace(",", ".")) for item in candidates)
    except ValueError:
        return None


def parse_int(text: str) -> int | None:
    candidates = re.findall(r"\d{3,6}", text.replace(" ", ""))
    if not candidates:
        return None
    return max(int(item) for item in candidates)


def parse_rank(text: str) -> str | None:
    normalized = text.upper().replace(" ", "")
    for rank in ("SSS+", "SSS", "SS+", "SS", "S+", "S", "AAA", "AA", "A"):
        if rank in normalized:
            return rank
    return None


def parse_pair(text: str) -> dict[str, int] | None:
    compact = text.replace(" ", "")
    match = re.search(r"(\d{2,5})/(\d{2,5})", compact)
    if not match:
        nums = re.findall(r"\d{2,5}", compact)
        if len(nums) < 2:
            return None
        return {"current": int(nums[0]), "total": int(nums[1])}
    return {"current": int(match.group(1)), "total": int(match.group(2))}


def parse_judgement(text: str) -> dict[str, int] | None:
    compact = text.replace(" ", "")
    numbers = [int(item) for item in re.findall(r"\d{1,4}", compact)]
    if len(numbers) < 5:
        return None
    # The crop is ordered top-to-bottom in the game UI.
    return {
        "critical_perfect": numbers[0],
        "perfect": numbers[1],
        "great": numbers[2],
        "good": numbers[3],
        "miss": numbers[4],
    }


def parse_fast_late(text: str) -> dict[str, int] | None:
    normalized = normalize_text(text).upper()
    fast = re.search(r"FAST\D{0,12}(\d{1,4})", normalized)
    late = re.search(r"LATE\D{0,12}(\d{1,4})", normalized)
    result = {}
    if fast:
        result["fast"] = int(fast.group(1))
    if late:
        result["late"] = int(late.group(1))
    return result or None


def item_center(item: dict[str, Any]) -> tuple[float, float] | None:
    box = item.get("box")
    if not isinstance(box, list) or not box:
        return None
    if len(box) == 4 and all(isinstance(value, (int, float)) for value in box):
        return ((float(box[0]) + float(box[2])) / 2, (float(box[1]) + float(box[3])) / 2)

    xs: list[float] = []
    ys: list[float] = []
    for point in box:
        if isinstance(point, list) and len(point) >= 2:
            xs.append(float(point[0]))
            ys.append(float(point[1]))
    if not xs or not ys:
        return None
    return sum(xs) / len(xs), sum(ys) / len(ys)


def normalize_label_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text or "").upper()
    value = value.replace("0", "O").replace("1", "I")
    return re.sub(r"[^A-Z]", "", value)


def parse_item_int(text: str) -> int | None:
    normalized = normalize_text(text)
    match = re.fullmatch(r"\d{1,4}", normalized)
    return int(match.group(0)) if match else None


def parse_column_int(text: str) -> int | None:
    normalized = normalize_text(text).upper()
    match = re.search(r"\d{1,4}", normalized)
    if match:
        return int(match.group(0))
    if re.fullmatch(r"[O0]+", normalized):
        return 0
    return None


def cluster_indexes(indexes: list[int], max_gap: int = 3) -> list[tuple[int, int]]:
    if not indexes:
        return []
    ranges: list[tuple[int, int]] = []
    start = end = indexes[0]
    for value in indexes[1:]:
        if value <= end + max_gap:
            end = value
        else:
            ranges.append((start, end))
            start = end = value
    ranges.append((start, end))
    return ranges


def is_judgement_grid_pixel(r: int, g: int, b: int) -> bool:
    brightness = (r + g + b) / 3
    return b >= 70 and r <= 125 and g <= 150 and b >= r + 8 and brightness <= 215


def detect_regular_dark_lines(
    image: Image.Image,
    axis: str,
    count: int,
) -> list[int] | None:
    gray = ImageOps.grayscale(image)
    width, height = gray.size
    pixels = gray.load()
    if axis == "vertical":
        length = width
        values = [
            sum(pixels[x, y] for y in range(int(height * 0.15), int(height * 0.88), 3))
            / len(range(int(height * 0.15), int(height * 0.88), 3))
            for x in range(width)
        ]
        local_radius = 30
        threshold = 8.0
        min_spacing = max(20, int(width * 0.012))
        min_step = width * 0.10
        max_step = width * 0.18
    else:
        length = height
        values = [
            sum(pixels[x, y] for x in range(int(width * 0.08), int(width * 0.92), 4))
            / len(range(int(width * 0.08), int(width * 0.92), 4))
            for y in range(height)
        ]
        local_radius = 20
        threshold = 5.0
        min_spacing = max(10, int(height * 0.018))
        min_step = height * 0.08
        max_step = height * 0.18

    smooth = [
        sum(values[max(0, index - 2):min(length, index + 3)])
        / len(values[max(0, index - 2):min(length, index + 3)])
        for index in range(length)
    ]
    scores = []
    for index, value in enumerate(smooth):
        left = max(0, index - local_radius)
        right = min(length, index + local_radius + 1)
        scores.append(sum(smooth[left:right]) / (right - left) - value)

    local_peaks = [
        index for index in range(4, length - 4)
        if scores[index] >= threshold
        and scores[index] == max(scores[index - 4:index + 5])
    ]
    candidates: list[int] = []
    for index in sorted(local_peaks, key=lambda value: scores[value], reverse=True):
        if all(abs(index - selected) >= min_spacing for selected in candidates):
            candidates.append(index)
    candidates.sort()
    if len(candidates) < count:
        return None

    best: tuple[float, list[int]] | None = None
    tolerance = length * 0.025
    for first in candidates:
        for last in candidates:
            if last <= first:
                continue
            step = (last - first) / (count - 1)
            if not min_step <= step <= max_step:
                continue
            selected: list[int] = []
            error = 0.0
            for offset in range(count):
                target = first + step * offset
                nearest = min(candidates, key=lambda value: abs(value - target))
                distance = abs(nearest - target)
                if distance > tolerance or nearest in selected:
                    break
                selected.append(nearest)
                error += distance / step
            if len(selected) != count:
                continue
            strength = sum(min(scores[value], 80.0) / 80.0 for value in selected)
            objective = error - strength * 0.08
            if best is None or objective < best[0]:
                best = (objective, selected)
    return best[1] if best else None


def detect_judgement_rows_and_columns(image: Image.Image) -> tuple[list[float], list[int]] | None:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()

    label_rows: list[int] = []
    for y in range(height):
        score = 0
        for x in range(int(width * 0.02), int(width * 0.26), 2):
            r, g, b = pixels[x, y]
            brightness = (r + g + b) / 3
            if b >= 60 and r <= 95 and g <= 130 and b >= r + 16 and brightness <= 165:
                score += 1
        if score >= width * 0.035:
            label_rows.append(y)

    label_ranges = [
        row_range for row_range in cluster_indexes(label_rows, max_gap=6)
        if row_range[1] - row_range[0] >= height * 0.28
    ]
    if label_ranges:
        label_top, label_bottom = max(label_ranges, key=lambda row_range: row_range[1] - row_range[0])
        row_step = (label_bottom - label_top) / 5
        row_centers = [label_top + row_step * (index + 0.5) for index in range(5)]
    else:
        row_centers = []

    horizontal: list[int] = []
    for y in range(height):
        score = 0
        for x in range(int(width * 0.05), int(width * 0.94), 2):
            if is_judgement_grid_pixel(*pixels[x, y]):
                score += 1
        if score >= width * 0.10:
            horizontal.append(y)
    h_lines = [
        (start + end) / 2
        for start, end in cluster_indexes(horizontal, max_gap=4)
        if end - start >= 2
    ]
    h_lines = sorted(h_lines)
    if not row_centers:
        h_lines = [
            line for line in h_lines
            if height * 0.08 <= line <= height * 0.96
        ]
        if len(h_lines) < 6:
            return None

        best_lines: list[float] | None = None
        best_error: float | None = None
        for start in range(0, len(h_lines) - 5):
            candidate = h_lines[start:start + 6]
            gaps = [b - a for a, b in zip(candidate, candidate[1:])]
            avg_gap = sum(gaps) / len(gaps)
            if avg_gap <= 0:
                continue
            error = sum(abs(gap - avg_gap) for gap in gaps) / avg_gap
            if best_error is None or error < best_error:
                best_error = error
                best_lines = candidate
        if not best_lines:
            return None
        row_centers = [(best_lines[index] + best_lines[index + 1]) / 2 for index in range(5)]

    regular_row_lines = detect_regular_dark_lines(image, "horizontal", 5)
    if regular_row_lines:
        row_step = sum(
            right - left for left, right in zip(regular_row_lines, regular_row_lines[1:])
        ) / 4
        detected_gaps = [right - left for left, right in zip(row_centers, row_centers[1:])]
        detected_step = sum(detected_gaps) / len(detected_gaps) if detected_gaps else 0
        if not row_centers or detected_step < row_step * 0.75 or detected_step > row_step * 1.25:
            row_boundaries = [*regular_row_lines, regular_row_lines[-1] + row_step]
            row_centers = [
                (row_boundaries[index] + row_boundaries[index + 1]) / 2
                for index in range(5)
            ]

    detected_columns = detect_regular_dark_lines(image, "vertical", 6)
    if detected_columns:
        col_bounds = detected_columns
    else:
        table_left = int(width * 0.25)
        table_right = int(width * 0.94)
        step = (table_right - table_left) / 5
        col_bounds = [int(round(table_left + step * index)) for index in range(6)]
    return row_centers, col_bounds


def recognize_judgement_row_centers(
    image: Image.Image,
    col_bounds: list[int],
    fallback_centers: list[float],
    output_dir: str | Path | None,
    engine: PaddleOcrEngine,
) -> list[float]:
    row_names = ("TAP", "HOLD", "SLIDE", "TOUCH", "BREAK")
    gaps = [right - left for left, right in zip(fallback_centers, fallback_centers[1:])]
    fallback_step = sum(gaps) / len(gaps) if gaps else image.height / 7
    column_widths = [right - left for left, right in zip(col_bounds, col_bounds[1:])]
    column_width = sum(column_widths) / len(column_widths)
    left = max(0, int(round(col_bounds[0] - column_width * 1.30)))
    right = max(left + 1, col_bounds[0] - max(5, int(image.width * 0.004)))
    top = max(0, int(round(fallback_centers[0] - fallback_step * 0.72)))
    bottom = min(image.height, int(round(fallback_centers[-1] + fallback_step * 0.72)))
    if right <= left or bottom <= top:
        return fallback_centers

    label_image = image.crop((left, top, right, bottom))
    prepared = prepare_ocr_image_data(label_image, "sub_judgement_column")
    if output_dir is not None:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        label_image.save(output / "row_labels.png")
        prepared.save(output / "row_labels_ocr.png")

    anchors: list[tuple[int, float]] = []
    for item in engine.read(prepared):
        label = normalize_label_text(str(item.get("text", "")))
        center = item_center(item)
        if center is None:
            continue
        for index, expected in enumerate(row_names):
            if label == expected:
                anchors.append((index, top + center[1] / 3))
                break
    if not anchors:
        return fallback_centers

    step_candidates = [
        (right_anchor - left_anchor) / (right_index - left_index)
        for left_pos, (left_index, left_anchor) in enumerate(anchors)
        for right_index, right_anchor in anchors[left_pos + 1:]
        if right_index > left_index and right_anchor > left_anchor
    ]
    if step_candidates:
        ordered_steps = sorted(step_candidates)
        fitted_step = ordered_steps[len(ordered_steps) // 2]
    else:
        fitted_step = fallback_step
    if not image.height * 0.05 <= fitted_step <= image.height * 0.20:
        fitted_step = fallback_step

    intercepts = sorted(center - index * fitted_step for index, center in anchors)
    intercept = intercepts[len(intercepts) // 2]
    fitted = [intercept + index * fitted_step for index in range(5)]
    if any(center < 0 or center >= image.height for center in fitted[:4]):
        return fallback_centers
    return fitted


def recognize_judgement_by_columns(
    table_image_source: str | Path | Image.Image,
    output_dir: str | Path | None,
    engine: PaddleOcrEngine,
    layout_hint: str | None = None,
) -> dict[str, dict[str, int]] | None:
    image = (
        table_image_source.convert("RGB")
        if isinstance(table_image_source, Image.Image)
        else Image.open(table_image_source).convert("RGB")
    )
    width, height = image.size
    if layout_hint == "dxnet":
        row_centers = [
            height * ratio
            for ratio in (0.269, 0.431, 0.592, 0.756, 0.919)
        ]
        col_bounds = [
            int(round(width * ratio))
            for ratio in (0.173, 0.340, 0.504, 0.671, 0.830, 0.997)
        ]
        detect_row_labels = False
    else:
        layout = detect_judgement_rows_and_columns(image)
        detect_row_labels = True
    if layout_hint != "dxnet" and not layout:
        # The cropper normalizes this field to the same table region. Use its
        # stable relative geometry when reflections hide the blue grid lines.
        row_centers = [height * (0.259 + index * 0.1205) for index in range(5)]
        col_bounds = [
            int(round(width * ratio))
            for ratio in (0.281, 0.410, 0.535, 0.659, 0.783, 0.906)
        ]
    elif layout_hint != "dxnet":
        row_centers, col_bounds = layout

    row_names = ("tap", "hold", "slide", "touch", "break")
    column_names = ("critical_perfect", "perfect", "great", "good", "miss")
    output = Path(output_dir) if output_dir is not None else None
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
    if detect_row_labels:
        row_centers = recognize_judgement_row_centers(
            image,
            col_bounds,
            row_centers,
            output,
            engine,
        )
    gaps = [b - a for a, b in zip(row_centers, row_centers[1:])]
    row_gap = sum(gaps) / len(gaps) if gaps else max(44, height / 8)
    top = max(0, int(round(row_centers[0] - row_gap * 0.75)))
    bottom = min(height, int(round(row_centers[-1] + row_gap * 0.75)))
    row_targets = {
        row_name: (center - top) * 3
        for row_name, center in zip(row_names, row_centers)
    }
    result: dict[str, dict[str, int]] = {row_name: {} for row_name in row_names}

    for index, column_name in enumerate(column_names):
        pad_x = max(5, int(width * 0.004))
        left = max(0, col_bounds[index] + pad_x)
        right = min(width, col_bounds[index + 1] - pad_x)
        if right <= left or bottom <= top:
            continue
        crop = image.crop((left, top, right, bottom))
        prepared = prepare_ocr_image_data(crop, "sub_judgement_column")
        if output is not None:
            crop.save(output / f"{column_name}.png")
            prepared.save(output / f"{column_name}_ocr.png")
        for item in engine.read(prepared):
            value = parse_column_int(str(item.get("text", "")))
            center = item_center(item)
            if value is None or center is None:
                continue
            _, y = center
            row_name, target = min(row_targets.items(), key=lambda pair: abs(pair[1] - y))
            if abs(target - y) <= row_gap * 3 * 0.58:
                result[row_name][column_name] = value

    for row_name, center_y in zip(row_names, row_centers):
        cell_top = max(0, int(round(center_y - row_gap * 0.32)))
        cell_bottom = min(height, int(round(center_y + row_gap * 0.32)))
        for index, column_name in enumerate(column_names):
            # MISS is especially prone to reading the hollow "0" as "8" when
            # OCR sees the whole column. Missing values are also rescanned as
            # isolated cells so small colored digits are not silently zeroed.
            existing_value = result[row_name].get(column_name)
            if existing_value is not None and not (
                column_name == "miss" and existing_value == 8
            ):
                continue
            pad_x = max(8, int(width * 0.008))
            cell_width = col_bounds[index + 1] - col_bounds[index]
            if column_name == "miss":
                cell_left = max(0, int(round(col_bounds[index] + cell_width * 0.40)))
            else:
                cell_left = max(0, col_bounds[index] + pad_x)
            cell_right = min(width, col_bounds[index + 1] - pad_x)
            if cell_right <= cell_left or cell_bottom <= cell_top:
                result[row_name][column_name] = 0
                continue
            cell = image.crop((cell_left, cell_top, cell_right, cell_bottom))
            prepared = prepare_ocr_image_data(cell, "sub_judgement_column")
            if output is not None:
                cell.save(output / f"{row_name}_{column_name}.png")
                prepared.save(output / f"{row_name}_{column_name}_ocr.png")
            cell_items = engine.read(prepared)
            value = None
            low_confidence_value = None
            for item in cell_items:
                candidate_value = parse_column_int(str(item.get("text", "")))
                if candidate_value is None:
                    continue
                score = item.get("score")
                if score is None or float(score) >= 0.90:
                    value = candidate_value
                    break
                if low_confidence_value is None:
                    low_confidence_value = candidate_value
            if value is None and column_name != "miss":
                # Small models can lose the left edge of dim colored digits.
                # Retry only failed cells with a wider grayscale crop; applying
                # grayscale to the full table regresses otherwise clear values.
                fallback_top = max(0, int(round(center_y - row_gap * 0.42)))
                fallback_bottom = min(height, int(round(center_y + row_gap * 0.42)))
                fallback_left = max(
                    0,
                    int(round(col_bounds[index] - cell_width * 0.12)),
                )
                fallback_right = min(
                    width,
                    int(round(col_bounds[index + 1] + cell_width * 0.06)),
                )
                fallback_cell = ImageOps.grayscale(
                    image.crop((
                        fallback_left,
                        fallback_top,
                        fallback_right,
                        fallback_bottom,
                    ))
                ).convert("RGB")
                fallback_prepared = prepare_ocr_image_data(
                    fallback_cell,
                    "sub_judgement_column",
                )
                if output is not None:
                    fallback_cell.save(output / f"{row_name}_{column_name}_gray.png")
                    fallback_prepared.save(
                        output / f"{row_name}_{column_name}_gray_ocr.png"
                    )
                for item in engine.read(fallback_prepared):
                    value = parse_column_int(str(item.get("text", "")))
                    if value is not None:
                        break
            if value is None:
                value = low_confidence_value
            if value is not None:
                result[row_name][column_name] = value
            else:
                result[row_name].setdefault(column_name, 0)

    for row_name in tuple(result):
        values = result[row_name]
        if (
            values.get("critical_perfect", 0) == 0
            and values.get("perfect", 0) == 0
            and values.get("great", 0) == 0
            and values.get("miss", 0) == 0
            and values.get("good", 0) > 0
        ):
            del result[row_name]

    result = {
        row: values
        for row, values in result.items()
        if values and any(int(value or 0) != 0 for value in values.values())
    }
    return result or None


def parse_sub_judgement_items(items: list[dict[str, Any]]) -> dict[str, dict[str, int]] | None:
    labels = {
        "TAP": "tap",
        "HOLD": "hold",
        "SLIDE": "slide",
        "TOUCH": "touch",
        "BREAK": "break",
    }
    rows: list[tuple[str, float, float]] = []
    numeric_items: list[tuple[float, float, int]] = []

    for item in items:
        center = item_center(item)
        if center is None:
            continue
        x, y = center
        text = str(item.get("text", ""))
        label = normalize_label_text(text)
        for expected, row_name in labels.items():
            if expected == label:
                rows.append((row_name, x, y))
                break

        value = parse_item_int(text)
        if value is not None:
            numeric_items.append((x, y, value))

    if not rows:
        return None

    rows.sort(key=lambda row: row[2])
    y_values = [row[2] for row in rows]
    gaps = [b - a for a, b in zip(y_values, y_values[1:]) if b > a]
    row_tolerance = max(54.0, (sum(gaps) / len(gaps) * 0.58) if gaps else 64.0)

    result: dict[str, dict[str, int]] = {}
    for row_name, label_x, label_y in rows:
        row_values = [
            (x, value)
            for x, y, value in numeric_items
            if x > label_x + 40 and abs(y - label_y) <= row_tolerance
        ]
        row_values.sort(key=lambda value: value[0])
        if len(row_values) < 5:
            continue
        values = [value for _, value in row_values[:5]]
        result[row_name] = {
            "critical_perfect": values[0],
            "perfect": values[1],
            "great": values[2],
            "good": values[3],
            "miss": values[4],
        }

    return result or None


def parse_sub_judgement(text: str) -> dict[str, dict[str, int]] | None:
    normalized = normalize_text(text).upper()
    labels = ("TAP", "HOLD", "SLIDE", "TOUCH", "BREAK")
    result: dict[str, dict[str, int]] = {}
    for label in labels:
        match = re.search(label + r"\D+(\d{1,4})\D+(\d{1,4})\D+(\d{1,4})\D+(\d{1,4})\D+(\d{1,4})", normalized)
        if not match:
            continue
        values = [int(item) for item in match.groups()]
        result[label.lower()] = {
            "critical_perfect": values[0],
            "perfect": values[1],
            "great": values[2],
            "good": values[3],
            "miss": values[4],
        }
    return result or None


def process_image_data(
    source_image: Image.Image,
    fields: Iterable[str],
    engine: PaddleOcrEngine,
) -> dict[str, Any]:
    """Run the production OCR pipeline entirely in memory."""
    metadata = crop_result_fields_in_memory(source_image)
    selected_fields = tuple(fields)
    ocr_fields: dict[str, dict[str, Any]] = {}

    for field in selected_fields:
        field_meta = metadata["fields"].get(field)
        if not field_meta:
            continue
        if field == "sub_judgement_table":
            table_image = field_meta["image"]
            if field_meta.get("layout_hint") != "dxnet":
                table_image = prepare_ocr_image_data(table_image, field)
            column_values = recognize_judgement_by_columns(
                table_image,
                None,
                engine,
                layout_hint=field_meta.get("layout_hint"),
            )
            ocr_fields[field] = {
                "items": [],
                "text": "",
                "column_values": column_values,
            }
            continue

        prepared = prepare_ocr_image_data(field_meta["image"], field)
        items = engine.read(prepared)
        ocr_fields[field] = {
            "items": items,
            "text": joined_text(items),
        }

    public_metadata = {
        "layout": metadata.get("layout", "arcade"),
        "screen": metadata["screen"],
        "fields": {
            name: {key: value for key, value in field.items() if key != "image"}
            for name, field in metadata["fields"].items()
        },
    }
    return {
        "source": "memory",
        "crop_metadata": public_metadata,
        "ocr_fields": ocr_fields,
        "parsed": parse_result(ocr_fields),
    }


def process_image(
    image_path: str | Path,
    crop_output_dir: str | Path,
    fields: Iterable[str],
    engine: PaddleOcrEngine,
) -> dict[str, Any]:
    metadata = crop_result_fields(image_path, crop_output_dir)
    selected_fields = tuple(fields)
    output_base = Path(crop_output_dir) / Path(image_path).stem / "ocr_input"
    ocr_fields: dict[str, dict[str, Any]] = {}

    for field in selected_fields:
        field_meta = metadata["fields"].get(field)
        if not field_meta:
            continue
        prepared = prepare_ocr_image(field_meta["path"], output_base / f"{field}.png", field)
        if field == "sub_judgement_table":
            table_source = (
                field_meta["path"]
                if field_meta.get("layout_hint") == "dxnet"
                else prepared
            )
            column_values = recognize_judgement_by_columns(
                table_source,
                output_base / "sub_judgement_columns",
                engine,
                layout_hint=field_meta.get("layout_hint"),
            )
            ocr_fields[field] = {
                "crop": field_meta["path"],
                "prepared": str(prepared),
                "items": [],
                "text": "",
                "column_values": column_values,
            }
            continue

        items = engine.read(prepared)
        field_result = {
            "crop": field_meta["path"],
            "prepared": str(prepared),
            "items": items,
            "text": joined_text(items),
        }
        ocr_fields[field] = field_result

    return {
        "source": str(image_path),
        "crop_metadata": metadata,
        "ocr_fields": ocr_fields,
        "parsed": parse_result(ocr_fields),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="OCR maimai result-screen field crops.")
    parser.add_argument("images", nargs="+", help="Image files or directories.")
    parser.add_argument("-o", "--output-dir", default="data/score_cropper_debug", help="Crop and OCR debug output directory.")
    parser.add_argument("--lang", default="japan", help="PaddleOCR language, for example japan, en, ch.")
    parser.add_argument(
        "--model-profile",
        choices=tuple(OCR_MODEL_PROFILES),
        default=os.getenv("SCORE_OCR_MODEL_PROFILE", "small"),
        help="OCR model size; small is the production default.",
    )
    parser.add_argument("--fields", default=",".join(OCR_FIELDS), help="Comma-separated field names to OCR.")
    parser.add_argument("--pretty", action="store_true", help="Print a compact human-readable summary.")
    args = parser.parse_args()

    fields = tuple(item.strip() for item in args.fields.split(",") if item.strip())
    engine = PaddleOcrEngine(lang=args.lang, model_profile=args.model_profile)
    results = [process_image(path, args.output_dir, fields, engine) for path in iter_images(args.images)]

    if args.pretty:
        for result in results:
            parsed = result["parsed"]
            print(result["source"])
            print(f"  title: {parsed.get('title')}")
            print(f"  achievement: {parsed.get('achievement')}")
            print(f"  sub_judgement: {parsed.get('sub_judgement')}")
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
