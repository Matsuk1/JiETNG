#!/usr/bin/env python3
"""
Prototype maimai result-screen cropper.

This script is intentionally standalone. It is not imported by main.py and does
not register any bot command. It detects the colorful circular result display in
arcade cabinet photos, then exports fixed relative regions for later OCR tests.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageEnhance, ImageOps


FIELD_BOXES = {
    # Relative to the detected inner result screen box.
    # Values are x1, y1, x2, y2 in 0..1 coordinates.
    "main_cover": (0.185, 0.155, 0.390, 0.320),
}


SUB_FIELD_BOXES = {
    # Relative to the upper LCD content, not the whole acrylic window.
    "sub_fast_late": (0.675, 0.505, 0.990, 0.955),
}


@dataclass(frozen=True)
class Box:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def clamp(self, width: int, height: int) -> "Box":
        return Box(
            max(0, min(width, self.left)),
            max(0, min(height, self.top)),
            max(0, min(width, self.right)),
            max(0, min(height, self.bottom)),
        )

    def to_tuple(self) -> tuple[int, int, int, int]:
        return self.left, self.top, self.right, self.bottom


def _sample_mask_points(image: Image.Image, step: int = 4) -> list[tuple[int, int]]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    points: list[tuple[int, int]] = []

    # The sub-monitor at the top is deliberately ignored. The lower half
    # contains the circular result UI in all supplied examples.
    y_start = int(height * 0.34)
    y_end = int(height * 0.96)
    x_margin = int(width * 0.035)

    for y in range(y_start, y_end, step):
        for x in range(x_margin, width - x_margin, step):
            r, g, b = pixels[x, y]
            mx = max(r, g, b)
            mn = min(r, g, b)
            saturation = mx - mn
            # Keep vivid result-screen pixels while dropping the white cabinet
            # glow and the dark plastic bezel.
            if mx >= 115 and saturation >= 42:
                # Blue/purple cabinet glow has high saturation too; require
                # enough red/yellow/green contribution to bias toward the UI.
                if r >= 90 or g >= 105:
                    points.append((x, y))
    return points


def _percentile(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    values = sorted(values)
    index = int((len(values) - 1) * ratio)
    return values[index]


def detect_result_screen(image: Image.Image) -> Box:
    image = ImageOps.exif_transpose(image)
    width, height = image.size
    points = _sample_mask_points(image)
    if len(points) < 200:
        raise ValueError("could not find enough colorful result-screen pixels")

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    raw = Box(
        _percentile(xs, 0.015),
        _percentile(ys, 0.015),
        _percentile(xs, 0.985),
        _percentile(ys, 0.985),
    )

    # The mask mostly captures colorful UI, not the whole round screen. Expand
    # it into a near-square inner-screen box and bias slightly upward so the
    # song title/header are retained.
    cx = (raw.left + raw.right) / 2
    cy = (raw.top + raw.bottom) / 2
    side = max(raw.width * 1.17, raw.height * 1.10)
    side = min(side, width * 0.90, height * 0.72)
    cy -= side * 0.025

    box = Box(
        int(round(cx - side / 2)),
        int(round(cy - side / 2)),
        int(round(cx + side / 2)),
        int(round(cy + side / 2)),
    ).clamp(width, height)

    return box


def _sample_sub_screen_points(image: Image.Image, step: int = 4) -> list[tuple[int, int]]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    points: list[tuple[int, int]] = []

    y_start = 0
    y_end = int(height * 0.255)
    x_margin = int(width * 0.12)

    for y in range(y_start, y_end, step):
        for x in range(x_margin, width - x_margin, step):
            r, g, b = pixels[x, y]
            mx = max(r, g, b)
            mn = min(r, g, b)
            saturation = mx - mn
            brightness = (r + g + b) / 3
            # The upper LCD is dim, but still has a rectangular block of lit
            # content. The cabinet and acrylic are darker or strongly pink.
            if brightness >= 82 and mx >= 95 and not (r > 150 and b > 120 and g < 85):
                if saturation <= 115 or b >= 85 or g >= 85:
                    points.append((x, y))
    return points


def _cluster_ranges(values: list[int], max_gap: int = 3) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    start: int | None = None
    previous: int | None = None
    for value in values:
        if start is None:
            start = previous = value
            continue
        if previous is not None and value - previous <= max_gap:
            previous = value
            continue
        ranges.append((start, previous if previous is not None else value))
        start = previous = value
    if start is not None:
        ranges.append((start, previous if previous is not None else start))
    return ranges


def _detect_sub_rail_top(image: Image.Image) -> int | None:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    rows: list[int] = []
    scores: dict[int, int] = {}

    x_start = int(width * 0.020)
    x_end = int(width * 0.980)
    y_start = int(height * 0.100)
    y_end = int(height * 0.300)
    sample_count = max(1, (x_end - x_start) // 4)
    threshold = max(260, int(sample_count * 0.38))

    for y in range(y_start, y_end):
        score = 0
        for x in range(x_start, x_end, 4):
            r, g, b = pixels[x, y]
            # The acrylic rail below the sub screen is a long pink/purple band.
            if r >= 85 and b >= 75 and g <= 105 and abs(r - b) <= 85:
                score += 1
        if score >= threshold:
            rows.append(y)
            scores[y] = score

    candidates = _cluster_ranges(rows, max_gap=3)
    candidates = [
        candidate for candidate in candidates
        if candidate[1] - candidate[0] >= 5
    ]
    if not candidates:
        return None

    def cluster_score(candidate: tuple[int, int]) -> int:
        start, end = candidate
        return sum(scores.get(y, 0) for y in range(start, end + 1))

    return max(candidates, key=cluster_score)[0]


def detect_sub_screen(image: Image.Image) -> Box:
    image = ImageOps.exif_transpose(image)
    width, height = image.size
    points = _sample_sub_screen_points(image)
    if len(points) < 200:
        return Box(
            int(width * 0.220),
            0,
            int(width * 0.790),
            int(height * 0.225),
        )

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    raw = Box(
        _percentile(xs, 0.060),
        _percentile(ys, 0.045),
        _percentile(xs, 0.955),
        _percentile(ys, 0.960),
    )

    pad_x = int(raw.width * 0.025)
    pad_top = max(int(raw.height * 0.090), int(height * 0.012))
    return Box(
        raw.left - pad_x,
        raw.top - pad_top,
        raw.right + pad_x,
        raw.bottom,
    ).clamp(width, height)


def _is_table_blue_pixel(r: int, g: int, b: int) -> bool:
    brightness = (r + g + b) / 3
    blue_line = b >= 90 and g >= 45 and b >= r + 18 and 42 <= brightness <= 215
    row_label = b >= 70 and r <= 85 and g <= 120 and b >= r + 22 and brightness <= 145
    return blue_line or row_label


def detect_sub_judgement_table(image: Image.Image, sub_screen: Box) -> Box | None:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()

    search = Box(
        max(0, sub_screen.left - int(sub_screen.width * 0.08)),
        sub_screen.top,
        min(width, sub_screen.left + int(sub_screen.width * 0.770)),
        sub_screen.bottom,
    )
    label_left = max(0, sub_screen.left - int(sub_screen.width * 0.100))
    label_right = min(width, sub_screen.left + int(sub_screen.width * 0.360))
    label_rows: list[int] = []
    label_points_by_row: dict[int, list[int]] = {}
    label_threshold = max(26, int((label_right - label_left) / 18))

    for y in range(search.top, search.bottom):
        score = 0
        row_points: list[int] = []
        for x in range(label_left, label_right, 2):
            r, g, b = pixels[x, y]
            brightness = (r + g + b) / 3
            if b >= 70 and r <= 88 and g <= 125 and b >= r + 22 and brightness <= 150:
                score += 1
                row_points.append(x)
        if score >= label_threshold:
            label_rows.append(y)
            label_points_by_row[y] = row_points

    ranges = [
        row_range for row_range in _cluster_ranges(label_rows, max_gap=5)
        if row_range[1] - row_range[0] >= 4
    ]
    if not ranges:
        return None

    label_range = max(ranges, key=lambda row_range: row_range[1] - row_range[0])
    top, bottom = label_range

    row_height = max(36, (bottom - top) / 5)
    label_index = ranges.index(label_range)
    for row_range in ranges[label_index + 1:]:
        gap = row_range[0] - bottom
        row_range_height = row_range[1] - row_range[0]
        if 0 < gap <= row_height * 0.85 and row_range_height >= row_height * 0.42:
            bottom = row_range[1]
            row_height = max(36, (bottom - top) / 5)
            continue
        break
    header_candidates = [
        row_range for row_range in ranges[:label_index]
        if top - row_range[1] <= max(95, int(row_height * 1.70))
    ]
    if header_candidates:
        table_top = header_candidates[0][0]
    else:
        table_top = int(round(top - row_height * 1.15))
    table_bottom = bottom

    label_xs: list[int] = []
    for y in range(top, bottom + 1):
        label_xs.extend(label_points_by_row.get(y, []))
    if len(label_xs) < 100:
        return None

    table_left = _percentile(label_xs, 0.005) - 12

    points: list[tuple[int, int]] = []
    for y in range(max(search.top, table_top), min(search.bottom, table_bottom), 2):
        for x in range(search.left, search.right, 2):
            r, g, b = pixels[x, y]
            if _is_table_blue_pixel(r, g, b):
                points.append((x, y))

    if len(points) < 200:
        return None

    xs = [point[0] for point in points]
    right = _percentile(xs, 0.975) + 8
    return Box(table_left, table_top - 4, right, table_bottom + 2).clamp(width, height)


def refine_sub_screen(sub_screen: Box, sub_judgement_table: Box | None) -> Box:
    if sub_judgement_table is None:
        return sub_screen
    bottom = min(
        sub_screen.bottom,
        sub_judgement_table.bottom + max(8, int(sub_screen.height * 0.010)),
    )
    return Box(sub_screen.left, sub_screen.top, sub_screen.right, bottom)


def main_content_box(screen: Box) -> Box:
    return relative_box(screen, (0.110, 0.110, 0.890, 0.705))


def detect_main_achievement(image: Image.Image, screen: Box) -> Box | None:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    search = relative_box(screen, (0.030, 0.255, 0.720, 0.455)).clamp(width, height)

    candidate_rows: list[int] = []
    row_scores: dict[int, int] = {}
    for y in range(search.top, search.bottom):
        score = 0
        for x in range(search.left, search.right, 4):
            r, g, b = pixels[x, y]
            brightness = (r + g + b) / 3
            if r >= 130 and g >= 55 and b <= 105 and r >= g + 12 and brightness >= 70:
                score += 1
        if score >= 40:
            candidate_rows.append(y)
            row_scores[y] = score

    row_ranges = [
        row_range for row_range in _cluster_ranges(candidate_rows, max_gap=4)
        if row_range[1] - row_range[0] >= 12
    ]
    if not row_ranges:
        return None

    digit_range = max(
        row_ranges,
        key=lambda row_range: sum(row_scores.get(y, 0) for y in range(row_range[0], row_range[1] + 1)),
    )
    points: list[tuple[int, int]] = []
    for y in range(digit_range[0], digit_range[1] + 1, 2):
        for x in range(search.left, search.right, 2):
            r, g, b = pixels[x, y]
            brightness = (r + g + b) / 3
            if r >= 130 and g >= 55 and b <= 105 and r >= g + 12 and brightness >= 70:
                points.append((x, y))

    if len(points) < 500:
        return None

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return Box(
        _percentile(xs, 0.010) - 20,
        _percentile(ys, 0.010) - 34,
        _percentile(xs, 0.990) + 20,
        _percentile(ys, 0.990) + 20,
    ).clamp(width, height)


def detect_main_title(image: Image.Image, screen: Box) -> Box | None:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    x_start = screen.left + int(screen.width * 0.180)
    x_end = screen.left + int(screen.width * 0.860)
    y_start = screen.top + int(screen.height * 0.120)
    y_end = screen.top + int(screen.height * 0.320)

    rows: list[int] = []
    row_scores: dict[int, int] = {}
    for y in range(y_start, y_end):
        score = 0
        for x in range(x_start, x_end, 4):
            r, g, b = pixels[x, y]
            mx = max(r, g, b)
            mn = min(r, g, b)
            brightness = (r + g + b) / 3
            if brightness <= 125 and mx - mn >= 22:
                score += 1
        if score >= 120:
            rows.append(y)
            row_scores[y] = score

    row_ranges = [
        row_range for row_range in _cluster_ranges(rows, max_gap=5)
        if row_range[1] - row_range[0] >= 12
    ]
    if not row_ranges:
        return None

    title_range = max(
        row_ranges,
        key=lambda row_range: sum(row_scores.get(y, 0) for y in range(row_range[0], row_range[1] + 1)),
    )
    title_height = title_range[1] - title_range[0]
    top = title_range[0] + 6
    if title_height >= 120:
        top = title_range[0] + int(title_height * 0.45)

    band_bottom = title_range[1] - 6
    band_height = max(1, band_bottom - top)
    column_scores: dict[int, int] = {}
    candidate_columns: list[int] = []
    bar_search_left = screen.left + int(screen.width * 0.140)
    bar_search_right = screen.left + int(screen.width * 0.900)
    threshold = max(2, int((band_height / 2) * 0.28))
    for x in range(bar_search_left, bar_search_right):
        score = 0
        for y in range(top, band_bottom, 2):
            r, g, b = pixels[x, y]
            brightness = (r + g + b) / 3
            saturation = max(r, g, b) - min(r, g, b)
            if brightness <= 150 and saturation >= 14:
                score += 1
        if score >= threshold:
            candidate_columns.append(x)
            column_scores[x] = score

    column_ranges = [
        column_range
        for column_range in _cluster_ranges(
            candidate_columns,
            max_gap=max(8, int(screen.width * 0.018)),
        )
        if column_range[1] - column_range[0] >= screen.width * 0.30
    ]
    if column_ranges:
        screen_center = (screen.left + screen.right) / 2
        bar_left, bar_right = min(
            column_ranges,
            key=lambda column_range: (
                abs((column_range[0] + column_range[1]) / 2 - screen_center),
                -sum(column_scores.get(x, 0) for x in range(column_range[0], column_range[1] + 1)),
            ),
        )
        horizontal_padding = max(8, int(screen.width * 0.010))
        left = max(
            bar_left + horizontal_padding,
            screen.left + int(screen.width * 0.350),
        )
        right = min(
            bar_right - horizontal_padding,
            screen.left + int(screen.width * 0.800),
        )
    else:
        left = screen.left + int(screen.width * 0.285)
        right = screen.left + int(screen.width * 0.790)

    return Box(
        left,
        top,
        right,
        band_bottom,
    ).clamp(width, height)


def relative_box(screen: Box, relative: tuple[float, float, float, float]) -> Box:
    x1, y1, x2, y2 = relative
    return Box(
        int(round(screen.left + screen.width * x1)),
        int(round(screen.top + screen.height * y1)),
        int(round(screen.left + screen.width * x2)),
        int(round(screen.top + screen.height * y2)),
    )


def sharpen_for_ocr(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    image = ImageEnhance.Contrast(image).enhance(1.35)
    image = ImageEnhance.Sharpness(image).enhance(1.45)
    return image


def is_dxnet_result_screenshot(image: Image.Image) -> bool:
    """Detect the vivid cyan mobile play-history page used by maimaidx.jp."""
    image = ImageOps.exif_transpose(image).convert("RGB")
    width, height = image.size
    if width <= 0 or height / width < 1.6:
        return False
    sample = image.resize((80, 80), Image.Resampling.BILINEAR)
    pixels = sample.load()
    vivid_cyan = sum(
        1
        for y in range(sample.height)
        for x in range(sample.width)
        if (
            pixels[x, y][0] < 120
            and pixels[x, y][1] > 140
            and pixels[x, y][2] > 180
        )
    )
    return vivid_cyan / (sample.width * sample.height) >= 0.08


def _dxnet_grid_line_pixel(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return (
        50 <= r <= 130
        and 115 <= g <= 170
        and 180 <= b <= 230
        and b - r >= 70
        and b - g >= 30
    )


def detect_dxnet_judgement_table(image: Image.Image) -> Box | None:
    """Find the stable blue outer border of the DX NET judgement table."""
    image = image.convert("RGB")
    width, height = image.size
    pixels = image.load()
    scan_right = min(width, int(round(width * 0.72)))
    minimum_score = max(40, int(round(width * 0.30)))
    candidate_rows: list[tuple[int, int]] = []

    for y in range(height):
        score = sum(
            _dxnet_grid_line_pixel(pixels[x, y])
            for x in range(scan_right)
        )
        if score >= minimum_score:
            candidate_rows.append((y, score))

    clusters: list[list[tuple[int, int]]] = []
    for y, score in candidate_rows:
        if not clusters or y > clusters[-1][-1][0] + 1:
            clusters.append([])
        clusters[-1].append((y, score))

    # The table is about 31% of the page width high. Pairing both outer
    # borders avoids depending on the page's vertical scroll position.
    borders = [
        max(cluster, key=lambda item: item[1])
        for cluster in clusters
    ]
    expected_height = width * 0.307
    candidates: list[tuple[float, int, int]] = []
    for top, top_score in borders:
        for bottom, bottom_score in borders:
            table_height = bottom - top
            if not width * 0.25 <= table_height <= width * 0.38:
                continue
            height_error = abs(table_height - expected_height) / width
            strength = min(top_score, bottom_score) / width
            candidates.append((height_error - strength * 0.08, top, bottom))

    if not candidates:
        return None
    _, top, bottom = min(candidates)
    return Box(
        int(round(width * 0.030)),
        top,
        int(round(width * 0.662)),
        bottom + 1,
    ).clamp(width, height)


def dxnet_result_field_boxes(image: Image.Image) -> dict[str, Box]:
    """Locate mobile DX NET fields relative to the judgement table."""
    width, height = image.size
    judgement_table = detect_dxnet_judgement_table(image)
    if judgement_table is None:
        raise ValueError("Could not locate the DX NET judgement table")

    def anchored_box(
        x1: float,
        top_offset: float,
        x2: float,
        bottom_offset: float,
    ) -> Box:
        box = Box(
            int(round(width * x1)),
            int(round(judgement_table.top + width * top_offset)),
            int(round(width * x2)),
            int(round(judgement_table.top + width * bottom_offset)),
        )
        if (
            box.left < 0
            or box.top < 0
            or box.right > width
            or box.bottom > height
        ):
            raise ValueError(
                "DX NET screenshot must include the title, achievement, and judgement table"
            )
        return box

    fields = {
        "main_title": anchored_box(0.035, -0.633, 0.850, -0.562),
        "main_achievement": anchored_box(0.465, -0.517, 0.800, -0.418),
        "sub_judgement_table": judgement_table,
    }
    if any(box.width <= 0 or box.height <= 0 for box in fields.values()):
        raise ValueError(
            "DX NET screenshot must include the title, achievement, and judgement table"
        )
    return fields


def _dxnet_fields_in_memory(image: Image.Image) -> dict:
    field_boxes = dxnet_result_field_boxes(image)
    fields = {}
    for name, field_box in field_boxes.items():
        fields[name] = {
            "image": sharpen_for_ocr(image.crop(field_box.to_tuple())),
            "left": field_box.left,
            "top": field_box.top,
            "right": field_box.right,
            "bottom": field_box.bottom,
            "detector": "dxnet_blue_grid_anchor",
            "layout_hint": "dxnet" if name == "sub_judgement_table" else None,
        }
    return {
        "layout": "dxnet",
        "screen": {
            "left": 0,
            "top": 0,
            "right": image.width,
            "bottom": image.height,
            "width": image.width,
            "height": image.height,
        },
        "fields": fields,
    }


def crop_result_fields_in_memory(source_image: Image.Image) -> dict:
    """Crop only OCR fields without creating debug files."""
    image = ImageOps.exif_transpose(source_image).convert("RGB")
    if is_dxnet_result_screenshot(image):
        return _dxnet_fields_in_memory(image)
    screen = detect_result_screen(image)
    sub_screen = detect_sub_screen(image)
    main_title = detect_main_title(image, screen)
    main_achievement = detect_main_achievement(image, screen)
    sub_judgement_table = detect_sub_judgement_table(image, sub_screen)

    if main_title is None:
        main_title = relative_box(screen, (0.285, 0.222, 0.790, 0.282)).clamp(
            image.width,
            image.height,
        )
        title_detector = "fallback_relative"
    else:
        title_detector = "title_bar"

    if main_achievement is None:
        main_achievement = relative_box(screen, (0.055, 0.300, 0.650, 0.395)).clamp(
            image.width,
            image.height,
        )
        achievement_detector = "fallback_relative"
    else:
        achievement_detector = "orange_digits"

    field_boxes = {
        "main_title": (main_title, title_detector),
        "main_achievement": (main_achievement, achievement_detector),
    }
    if sub_judgement_table is not None:
        field_boxes["sub_judgement_table"] = (sub_judgement_table, "blue_grid")

    fields = {}
    for name, (field_box, detector) in field_boxes.items():
        fields[name] = {
            "image": sharpen_for_ocr(image.crop(field_box.to_tuple())),
            "left": field_box.left,
            "top": field_box.top,
            "right": field_box.right,
            "bottom": field_box.bottom,
            "detector": detector,
        }

    return {
        "screen": {
            "left": screen.left,
            "top": screen.top,
            "right": screen.right,
            "bottom": screen.bottom,
            "width": screen.width,
            "height": screen.height,
        },
        "fields": fields,
    }


def crop_result_fields(image_path: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict:
    source = Path(image_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    image = Image.open(source)
    image = ImageOps.exif_transpose(image).convert("RGB")
    if is_dxnet_result_screenshot(image):
        metadata = _dxnet_fields_in_memory(image)
        sample_dir = output / source.stem
        if sample_dir.exists():
            shutil.rmtree(sample_dir)
        sample_dir.mkdir(parents=True, exist_ok=True)
        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)
        result = {
            "source": str(source),
            "layout": "dxnet",
            "screen": metadata["screen"],
            "fields": {},
        }
        for name, field in metadata["fields"].items():
            crop_path = sample_dir / f"{name}.png"
            field["image"].save(crop_path)
            box = Box(field["left"], field["top"], field["right"], field["bottom"])
            draw.rectangle(box.to_tuple(), outline=(255, 80, 0), width=2)
            draw.text((box.left + 4, box.top + 4), name, fill=(255, 255, 255))
            result["fields"][name] = {
                key: value
                for key, value in field.items()
                if key != "image"
            }
            result["fields"][name]["path"] = str(crop_path)
        overlay.save(sample_dir / "debug_overlay.png")
        with open(sample_dir / "metadata.json", "w", encoding="utf-8") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=2)
        return result
    screen = detect_result_screen(image)
    sub_screen = detect_sub_screen(image)
    stem = source.stem
    sample_dir = output / stem
    if sample_dir.exists():
        shutil.rmtree(sample_dir)
    sample_dir.mkdir(parents=True, exist_ok=True)

    content_screen = main_content_box(screen).clamp(image.width, image.height)
    main_title = detect_main_title(image, screen)
    main_achievement = detect_main_achievement(image, screen)
    sub_judgement_table = detect_sub_judgement_table(image, sub_screen)
    refined_sub_screen = refine_sub_screen(sub_screen, sub_judgement_table).clamp(image.width, image.height)
    image.crop(screen.to_tuple()).save(sample_dir / "screen.png")
    image.crop(content_screen.to_tuple()).save(sample_dir / "main_content.png")
    image.crop(refined_sub_screen.to_tuple()).save(sample_dir / "sub_screen.png")

    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    draw.rectangle(screen.to_tuple(), outline=(0, 255, 80), width=max(4, image.width // 300))
    draw.rectangle(content_screen.to_tuple(), outline=(0, 255, 180), width=max(3, image.width // 420))

    result = {
        "source": str(source),
        "screen": {
            "left": screen.left,
            "top": screen.top,
            "right": screen.right,
            "bottom": screen.bottom,
            "width": screen.width,
            "height": screen.height,
        },
        "main_content": {
            "left": content_screen.left,
            "top": content_screen.top,
            "right": content_screen.right,
            "bottom": content_screen.bottom,
            "width": content_screen.width,
            "height": content_screen.height,
        },
        "sub_screen": {
            "left": refined_sub_screen.left,
            "top": refined_sub_screen.top,
            "right": refined_sub_screen.right,
            "bottom": refined_sub_screen.bottom,
            "width": refined_sub_screen.width,
            "height": refined_sub_screen.height,
        },
        "sub_screen_raw": {
            "left": sub_screen.left,
            "top": sub_screen.top,
            "right": sub_screen.right,
            "bottom": sub_screen.bottom,
            "width": sub_screen.width,
            "height": sub_screen.height,
        },
        "fields": {},
    }

    draw.rectangle(refined_sub_screen.to_tuple(), outline=(0, 180, 255), width=max(4, image.width // 300))

    all_fields = [(screen, FIELD_BOXES), (refined_sub_screen, SUB_FIELD_BOXES)]
    for base_box, field_defs in all_fields:
        for name, rel in field_defs.items():
            field_box = relative_box(base_box, rel).clamp(image.width, image.height)
            crop = sharpen_for_ocr(image.crop(field_box.to_tuple()))
            crop_path = sample_dir / f"{name}.png"
            crop.save(crop_path)
            draw.rectangle(field_box.to_tuple(), outline=(255, 80, 0), width=max(2, image.width // 500))
            draw.text((field_box.left + 4, field_box.top + 4), name, fill=(255, 255, 255))
            result["fields"][name] = {
                "path": str(crop_path),
                "left": field_box.left,
                "top": field_box.top,
                "right": field_box.right,
                "bottom": field_box.bottom,
            }

    if main_title is not None:
        crop = sharpen_for_ocr(image.crop(main_title.to_tuple()))
        crop_path = sample_dir / "main_title.png"
        crop.save(crop_path)
        draw.rectangle(main_title.to_tuple(), outline=(255, 80, 0), width=max(2, image.width // 500))
        draw.text((main_title.left + 4, main_title.top + 4), "main_title", fill=(255, 255, 255))
        result["fields"]["main_title"] = {
            "path": str(crop_path),
            "left": main_title.left,
            "top": main_title.top,
            "right": main_title.right,
            "bottom": main_title.bottom,
            "detector": "title_bar",
        }
    else:
        fallback = relative_box(screen, (0.285, 0.222, 0.790, 0.282)).clamp(image.width, image.height)
        crop = sharpen_for_ocr(image.crop(fallback.to_tuple()))
        crop_path = sample_dir / "main_title.png"
        crop.save(crop_path)
        draw.rectangle(fallback.to_tuple(), outline=(255, 80, 0), width=max(2, image.width // 500))
        draw.text((fallback.left + 4, fallback.top + 4), "main_title", fill=(255, 255, 255))
        result["fields"]["main_title"] = {
            "path": str(crop_path),
            "left": fallback.left,
            "top": fallback.top,
            "right": fallback.right,
            "bottom": fallback.bottom,
            "detector": "fallback_relative",
        }

    if main_achievement is not None:
        crop = sharpen_for_ocr(image.crop(main_achievement.to_tuple()))
        crop_path = sample_dir / "main_achievement.png"
        crop.save(crop_path)
        draw.rectangle(main_achievement.to_tuple(), outline=(255, 80, 0), width=max(2, image.width // 500))
        draw.text((main_achievement.left + 4, main_achievement.top + 4), "main_achievement", fill=(255, 255, 255))
        result["fields"]["main_achievement"] = {
            "path": str(crop_path),
            "left": main_achievement.left,
            "top": main_achievement.top,
            "right": main_achievement.right,
            "bottom": main_achievement.bottom,
            "detector": "orange_digits",
        }
    else:
        fallback = relative_box(screen, (0.055, 0.300, 0.650, 0.395)).clamp(image.width, image.height)
        crop = sharpen_for_ocr(image.crop(fallback.to_tuple()))
        crop_path = sample_dir / "main_achievement.png"
        crop.save(crop_path)
        draw.rectangle(fallback.to_tuple(), outline=(255, 80, 0), width=max(2, image.width // 500))
        draw.text((fallback.left + 4, fallback.top + 4), "main_achievement", fill=(255, 255, 255))
        result["fields"]["main_achievement"] = {
            "path": str(crop_path),
            "left": fallback.left,
            "top": fallback.top,
            "right": fallback.right,
            "bottom": fallback.bottom,
            "detector": "fallback_relative",
        }

    if sub_judgement_table is not None:
        crop = sharpen_for_ocr(image.crop(sub_judgement_table.to_tuple()))
        crop_path = sample_dir / "sub_judgement_table.png"
        crop.save(crop_path)
        draw.rectangle(sub_judgement_table.to_tuple(), outline=(255, 80, 0), width=max(2, image.width // 500))
        draw.text((sub_judgement_table.left + 4, sub_judgement_table.top + 4), "sub_judgement_table", fill=(255, 255, 255))
        result["fields"]["sub_judgement_table"] = {
            "path": str(crop_path),
            "left": sub_judgement_table.left,
            "top": sub_judgement_table.top,
            "right": sub_judgement_table.right,
            "bottom": sub_judgement_table.bottom,
            "detector": "blue_grid",
        }
    else:
        fallback = relative_box(sub_screen, (0.050, 0.285, 0.675, 0.720)).clamp(image.width, image.height)
        crop = sharpen_for_ocr(image.crop(fallback.to_tuple()))
        crop_path = sample_dir / "sub_judgement_table.png"
        crop.save(crop_path)
        draw.rectangle(fallback.to_tuple(), outline=(255, 80, 0), width=max(2, image.width // 500))
        draw.text((fallback.left + 4, fallback.top + 4), "sub_judgement_table", fill=(255, 255, 255))
        result["fields"]["sub_judgement_table"] = {
            "path": str(crop_path),
            "left": fallback.left,
            "top": fallback.top,
            "right": fallback.right,
            "bottom": fallback.bottom,
            "detector": "fallback_relative",
        }

    overlay.save(sample_dir / "debug_overlay.png")
    with open(sample_dir / "metadata.json", "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)

    return result


def iter_images(paths: Iterable[str]) -> Iterable[Path]:
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            for item in sorted(path.iterdir()):
                if item.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                    yield item
        else:
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Crop maimai result-screen fields for OCR prototyping.")
    parser.add_argument("images", nargs="+", help="Image files or directories.")
    parser.add_argument("-o", "--output-dir", default="data/score_cropper_debug", help="Output directory.")
    parser.add_argument("--json", action="store_true", help="Print JSON metadata to stdout.")
    args = parser.parse_args()

    results = []
    for image_path in iter_images(args.images):
        results.append(crop_result_fields(image_path, args.output_dir))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"{item['source']} -> {Path(args.output_dir) / Path(item['source']).stem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
