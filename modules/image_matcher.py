"""
曲绘图片识别模块。

流程：
1. 从 dxdata 的 cover_name / cover_url 建立曲绘索引。
2. 使用 pHash + dHash 快速筛出候选。
3. 对候选使用 SIFT/ORB 或缩略图相似度复核。
"""
from __future__ import annotations

import json
import logging
import os
import hashlib
import threading
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Iterable

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

try:
    import cv2
    import numpy as np
except Exception:  # pragma: no cover - optional dependency fallback
    cv2 = None
    np = None

from modules.config_loader import COVERS_DIR
from modules.image_cache import get_cover_image


logger = logging.getLogger(__name__)

INDEX_FILE = "./data/image_match_index.json"
PHASH_SIZE = 8
PHASH_HIGHFREQ_SIZE = 32
DHASH_SIZE = 16
HASH_CANDIDATE_LIMIT = 80
DOWNLOAD_WORKERS = 12
HASH_SCORE_THRESHOLD = 0.70
MATCH_SCORE_THRESHOLD = 0.76

_index_lock = threading.RLock()
_index_cache: dict[str, Any] = {
    "signature": None,
    "entries": [],
}


@dataclass(frozen=True)
class CoverEntry:
    cover_name: str
    cover_url: str
    song_id: str
    song: dict[str, Any]
    phash: Any
    dhash: Any
    path: str


@dataclass(frozen=True)
class ImageRecognitionResult:
    song: dict[str, Any]
    cover_name: str
    score: float
    method: str
    hash_score: float
    verify_score: float


def recognize_songs_from_image(
    input_image: Image.Image,
    songs_data: list[dict[str, Any]],
    covers_dir: str | None = None,
    max_results: int = 3,
) -> list[ImageRecognitionResult]:
    """识别图片中的曲绘，返回按置信度降序排列的歌曲候选。"""
    covers_dir = covers_dir or COVERS_DIR
    entries = _load_cover_index(songs_data, covers_dir)
    if not entries:
        logger.warning("[ImageMatcher] cover index is empty")
        return []

    variants = _make_input_variants(input_image)
    hash_candidates = _rank_hash_candidates(variants, entries)
    if not hash_candidates:
        return []

    input_cv_variants = [_pil_to_cv2(img) for img in variants] if cv2 is not None else []
    input_features = [_extract_features(cv_img) for cv_img in input_cv_variants] if cv2 is not None else []

    results: list[ImageRecognitionResult] = []
    seen_covers: set[str] = set()
    for hash_score, entry in hash_candidates[:HASH_CANDIDATE_LIMIT]:
        if entry.cover_name in seen_covers:
            continue
        seen_covers.add(entry.cover_name)

        cover_img = _open_cover(entry.path)
        if cover_img is None:
            continue

        verify_score, verify_method = _verify_candidate(variants, input_cv_variants, input_features, cover_img)
        score = max(hash_score * 0.92, hash_score * 0.72 + verify_score * 0.28)
        method = "hash" if verify_method == "none" else f"hash+{verify_method}"
        if score >= MATCH_SCORE_THRESHOLD or hash_score >= 0.90:
            results.append(ImageRecognitionResult(
                song=entry.song,
                cover_name=entry.cover_name,
                score=round(score, 4),
                method=method,
                hash_score=round(hash_score, 4),
                verify_score=round(verify_score, 4),
            ))

    results.sort(key=lambda item: item.score, reverse=True)
    return _dedupe_song_results(results)[:max_results]


def warm_image_recognition_index(songs_data: list[dict[str, Any]], covers_dir: str | None = None) -> int:
    """预热曲绘识别索引，返回可用曲绘数量。"""
    entries = _load_cover_index(songs_data, covers_dir or COVERS_DIR)
    return len(entries)


def find_song_by_cover(
    input_image: Image.Image,
    songs_data: list[dict[str, Any]],
    covers_dir: str | None = None,
    return_multiple: bool = False,
    max_results: int = 3,
):
    """兼容旧接口：按曲绘图片查找歌曲。"""
    results = recognize_songs_from_image(input_image, songs_data, covers_dir, max_results)
    if return_multiple:
        return [item.song for item in results]
    return results[0].song if results else None


def _load_cover_index(songs_data: list[dict[str, Any]], covers_dir: str) -> list[CoverEntry]:
    os.makedirs(covers_dir, exist_ok=True)
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)

    unique_covers = _unique_cover_rows(songs_data)
    signature = _index_signature(unique_covers, covers_dir)

    with _index_lock:
        if _index_cache["signature"] == signature:
            return _index_cache["entries"]

        stored = _read_stored_index()
        stored_items = stored.get("items", {}) if stored.get("signature") == signature else {}
        built_entries, changed_items = _build_entries(unique_covers, covers_dir, stored_items)

        if changed_items:
            _write_stored_index(signature, changed_items)

        _index_cache["signature"] = signature
        _index_cache["entries"] = built_entries
        logger.info("[ImageMatcher] cover index loaded: %s entries", len(built_entries))
        return built_entries


def _unique_cover_rows(songs_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for song in songs_data:
        cover_name = _normalize_cover_name(song.get("cover_name"))
        if not cover_name:
            continue
        rows.setdefault(cover_name, {
            "cover_name": cover_name,
            "cover_url": song.get("cover_url") or "",
            "song_id": str(song.get("id") or ""),
            "song": song,
        })
    return list(rows.values())


def _index_signature(rows: list[dict[str, Any]], covers_dir: str) -> str:
    names = ",".join(sorted(row["cover_name"] for row in rows))
    digest = hashlib.sha1(names.encode("utf-8")).hexdigest()
    return f"{os.path.abspath(covers_dir)}:{len(rows)}:{digest}"


def _build_entries(rows: list[dict[str, Any]], covers_dir: str, stored_items: dict[str, Any]):
    entries: list[CoverEntry] = []
    changed_items = dict(stored_items)
    pending_rows = []

    for row in rows:
        cover_name = row["cover_name"]
        path = os.path.join(covers_dir, cover_name)
        item = stored_items.get(cover_name)
        mtime = _file_mtime(path)
        if item and item.get("mtime") == mtime and item.get("phash") and item.get("dhash"):
            entry = _entry_from_stored(row, path, item)
            if entry is not None:
                entries.append(entry)
                continue
        pending_rows.append(row)

    if pending_rows:
        with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
            futures = {
                executor.submit(_prepare_cover_entry, row, covers_dir): row
                for row in pending_rows
            }
            for future in as_completed(futures):
                entry, item = future.result()
                if entry is None or item is None:
                    continue
                entries.append(entry)
                changed_items[entry.cover_name] = item

    entries.sort(key=lambda item: item.cover_name)
    return entries, changed_items


def _prepare_cover_entry(row: dict[str, Any], covers_dir: str):
    cover_name = row["cover_name"]
    path = os.path.join(covers_dir, cover_name)
    img = _open_cover(path)
    if img is None:
        img = get_cover_image(row.get("cover_url"), cover_name)
    if img is None:
        return None, None

    try:
        phash = _phash(img)
        dhash = _dhash(img)
        item = {
            "mtime": _file_mtime(path),
            "phash": format(phash, "016x"),
            "dhash": format(dhash, "064x"),
        }
        return CoverEntry(
            cover_name=cover_name,
            cover_url=row.get("cover_url") or "",
            song_id=row.get("song_id") or "",
            song=row["song"],
            phash=phash,
            dhash=dhash,
            path=path,
        ), item
    except Exception as e:
        logger.debug("[ImageMatcher] failed to hash cover %s: %s", cover_name, e)
        return None, None


def _entry_from_stored(row: dict[str, Any], path: str, item: dict[str, Any]):
    try:
        return CoverEntry(
            cover_name=row["cover_name"],
            cover_url=row.get("cover_url") or "",
            song_id=row.get("song_id") or "",
            song=row["song"],
            phash=int(item["phash"], 16),
            dhash=int(item["dhash"], 16),
            path=path,
        )
    except Exception:
        return None


def _read_stored_index() -> dict[str, Any]:
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def _write_stored_index(signature: str, items: dict[str, Any]) -> None:
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as file:
            json.dump({"signature": signature, "items": items}, file, ensure_ascii=False)
    except Exception as e:
        logger.warning("[ImageMatcher] failed to write index cache: %s", e)


def _rank_hash_candidates(variants: list[Image.Image], entries: list[CoverEntry]):
    variant_hashes = []
    for img in variants:
        variant_hashes.append((_phash(img), _dhash(img)))

    phash_bits = PHASH_SIZE * PHASH_SIZE
    dhash_bits = DHASH_SIZE * DHASH_SIZE
    candidates = []
    for entry in entries:
        best_score = 0.0
        for phash, dhash in variant_hashes:
            p_score = _hash_similarity(phash, entry.phash, phash_bits)
            d_score = _hash_similarity(dhash, entry.dhash, dhash_bits)
            score = p_score * 0.72 + d_score * 0.28
            if score > best_score:
                best_score = score
        if best_score >= HASH_SCORE_THRESHOLD:
            candidates.append((best_score, entry))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def _hash_similarity(left: int, right: int, bits: int) -> float:
    return 1.0 - ((left ^ right).bit_count() / bits)


def _dhash(image: Image.Image) -> int:
    gray = image.convert("L").resize((DHASH_SIZE + 1, DHASH_SIZE), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    value = 0
    for y in range(DHASH_SIZE):
        row = y * (DHASH_SIZE + 1)
        for x in range(DHASH_SIZE):
            value = (value << 1) | int(pixels[row + x] > pixels[row + x + 1])
    return value


def _phash(image: Image.Image) -> int:
    gray = image.convert("L").resize(
        (PHASH_HIGHFREQ_SIZE, PHASH_HIGHFREQ_SIZE),
        Image.Resampling.LANCZOS,
    )
    if cv2 is not None and np is not None:
        pixels = np.asarray(gray, dtype=np.float32)
        dct = cv2.dct(pixels)[:PHASH_SIZE, :PHASH_SIZE]
        values = dct.flatten()[1:]
        median = float(np.median(values))
        bits = dct.flatten() >= median
        value = 0
        for bit in bits:
            value = (value << 1) | int(bit)
        return value

    pixels = list(gray.getdata())
    coeffs = []
    for v in range(PHASH_SIZE):
        for u in range(PHASH_SIZE):
            total = 0.0
            for y in range(PHASH_HIGHFREQ_SIZE):
                row = y * PHASH_HIGHFREQ_SIZE
                cy = _dct_cos(y, v)
                for x in range(PHASH_HIGHFREQ_SIZE):
                    total += pixels[row + x] * _dct_cos(x, u) * cy
            coeffs.append(total)
    median = _median(coeffs[1:])
    value = 0
    for coeff in coeffs:
        value = (value << 1) | int(coeff >= median)
    return value


_DCT_COS_CACHE: dict[tuple[int, int], float] = {}


def _dct_cos(pos: int, freq: int) -> float:
    key = (pos, freq)
    cached = _DCT_COS_CACHE.get(key)
    if cached is not None:
        return cached
    value = math.cos(((2 * pos + 1) * freq * math.pi) / (2 * PHASH_HIGHFREQ_SIZE))
    _DCT_COS_CACHE[key] = value
    return value


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _verify_candidate(
    variants: list[Image.Image],
    input_cv_variants: list[Any],
    input_features: list[Any],
    cover_img: Image.Image,
):
    cv_score = _feature_verify_score(input_cv_variants, input_features, cover_img)
    if cv_score > 0:
        return cv_score, "sift"
    return _thumbnail_similarity_score(variants, cover_img), "thumb"


def _feature_verify_score(input_cv_variants: list[Any], input_features: list[Any], cover_img: Image.Image) -> float:
    if cv2 is None or np is None:
        return 0.0

    cover_cv = _pil_to_cv2(cover_img)
    cover_kp, cover_desc, detector_name = _extract_features(cover_cv)
    if cover_desc is None:
        return 0.0

    best = 0.0
    for input_kp, input_desc, _ in input_features:
        if input_desc is None:
            continue
        score = _match_feature_score(input_kp, input_desc, cover_kp, cover_desc, detector_name)
        if score > best:
            best = score
    return best


def _extract_features(image_cv):
    if cv2 is None or image_cv is None:
        return None, None, "none"
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    try:
        if hasattr(cv2, "SIFT_create"):
            detector = cv2.SIFT_create(nfeatures=900)
            kp, desc = detector.detectAndCompute(gray, None)
            return kp, desc, "sift"
    except Exception:
        pass

    detector = cv2.ORB_create(nfeatures=1200)
    kp, desc = detector.detectAndCompute(gray, None)
    return kp, desc, "orb"


def _match_feature_score(kp1, desc1, kp2, desc2, detector_name: str) -> float:
    if desc1 is None or desc2 is None or len(kp1) < 8 or len(kp2) < 8:
        return 0.0
    try:
        if detector_name == "sift":
            matcher = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=40))
            matches = matcher.knnMatch(desc1, desc2, k=2)
            ratio = 0.68
        else:
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
            matches = matcher.knnMatch(desc1, desc2, k=2)
            ratio = 0.76

        good = []
        for pair in matches:
            if len(pair) == 2 and pair[0].distance < ratio * pair[1].distance:
                good.append(pair[0])
        if len(good) < 8:
            return 0.0

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 4.0)
        if mask is None:
            return 0.0
        geometric = int(mask.sum())
        if geometric < 8:
            return 0.0
        support = min(1.0, geometric / 28)
        quality = geometric / max(1, len(good))
        coverage = geometric / max(1, min(len(kp1), len(kp2)))
        return min(1.0, 0.48 + support * 0.28 + quality * 0.18 + coverage * 0.06)
    except Exception:
        return 0.0


def _thumbnail_similarity_score(variants: list[Image.Image], cover_img: Image.Image) -> float:
    cover = cover_img.convert("RGB").resize((128, 128), Image.Resampling.LANCZOS)
    best = 0.0
    for variant in variants:
        img = variant.convert("RGB").resize((128, 128), Image.Resampling.LANCZOS)
        diff = ImageChops.difference(img, cover)
        stat = ImageStat.Stat(diff)
        rms = sum(value ** 2 for value in stat.rms) ** 0.5 / (255 * (3 ** 0.5))
        best = max(best, 1.0 - rms)
    return best


def _make_input_variants(image: Image.Image) -> list[Image.Image]:
    original = ImageOps.exif_transpose(image).convert("RGB")
    base = _trim_border(original)
    variants = [original]
    if base.size != original.size:
        variants.append(base)
    variants.extend(_maimai_result_cover_crops(base))
    variants.extend(_rank_small_square_crops(base))
    w, h = base.size
    side = min(w, h)
    if side > 0 and abs(w - h) > max(12, side * 0.04):
        for crop in _square_crops(base, side):
            variants.append(crop)
    if side > 80:
        inset = int(side * 0.04)
        if w - inset * 2 > 40 and h - inset * 2 > 40:
            variants.append(base.crop((inset, inset, w - inset, h - inset)))

    unique = []
    seen = set()
    for variant in variants:
        key = _image_variant_key(variant)
        if key not in seen:
            seen.add(key)
            unique.append(variant)
    return unique[:64]


def _image_variant_key(image: Image.Image) -> tuple[Any, ...]:
    thumb = image.convert("L").resize((12, 12), Image.Resampling.BILINEAR)
    return image.size + tuple(thumb.getdata())


def _maimai_result_cover_crops(image: Image.Image) -> list[Image.Image]:
    """针对 maimai 结算画面的小曲绘位置生成强先验候选。"""
    w, h = image.size
    short = min(w, h)
    candidates = []

    if h >= w:
        anchor_boxes = [
            (0.245, 0.430, 0.060),
            (0.265, 0.450, 0.070),
            (0.285, 0.465, 0.080),
            (0.225, 0.410, 0.090),
            (0.305, 0.485, 0.100),
        ]
    else:
        anchor_boxes = [
            (0.430, 0.245, 0.060),
            (0.450, 0.265, 0.070),
            (0.465, 0.285, 0.080),
            (0.410, 0.225, 0.090),
            (0.485, 0.305, 0.100),
        ]

    for cx_ratio, cy_ratio, side_ratio in anchor_boxes:
        side = int(short * side_ratio)
        cx = int(w * cx_ratio)
        cy = int(h * cy_ratio)
        candidates.extend(_nearby_square_crops(image, cx, cy, side))
    return candidates


def _nearby_square_crops(image: Image.Image, cx: int, cy: int, side: int) -> list[Image.Image]:
    if side < 40:
        return []
    offsets = [-0.35, 0, 0.35]
    crops = []
    for oy in offsets:
        for ox in offsets:
            x1 = int(cx - side / 2 + side * ox)
            y1 = int(cy - side / 2 + side * oy)
            crop = _bounded_square_crop(image, x1, y1, side)
            if crop is not None:
                crops.append(crop)
    return crops


def _rank_small_square_crops(image: Image.Image) -> list[Image.Image]:
    """从整张照片中找最像小曲绘的高信息量正方形区域。"""
    w, h = image.size
    short = min(w, h)
    if short < 300:
        return []

    scale = min(1.0, 720 / max(w, h))
    scan = image.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
    sw, sh = scan.size
    sshort = min(sw, sh)

    scored = []
    side_ratios = (0.045, 0.055, 0.065, 0.08, 0.10, 0.13, 0.16)
    for ratio in side_ratios:
        side = max(32, int(sshort * ratio))
        step = max(18, int(side * 0.65))
        for y in range(0, max(1, sh - side + 1), step):
            for x in range(0, max(1, sw - side + 1), step):
                crop = scan.crop((x, y, x + side, y + side))
                score = _small_cover_likelihood(crop, x / sw, y / sh)
                if score > 0.30:
                    scored.append((score, x, y, side))

    scored.sort(key=lambda item: item[0], reverse=True)
    crops = []
    for _, x, y, side in scored[:36]:
        ox = int(x / scale)
        oy = int(y / scale)
        oside = int(side / scale)
        crop = _bounded_square_crop(image, ox, oy, oside)
        if crop is not None:
            crops.append(crop)
    return crops


def _small_cover_likelihood(crop: Image.Image, x_ratio: float, y_ratio: float) -> float:
    hsv = crop.convert("HSV")
    stat = ImageStat.Stat(hsv)
    saturation = stat.mean[1] / 255
    value_std = stat.stddev[2] / 128
    edge = ImageStat.Stat(crop.convert("L").filter(ImageFilter.FIND_EDGES)).mean[0] / 255
    position = 1.0
    if 0.10 <= x_ratio <= 0.45 and 0.25 <= y_ratio <= 0.58:
        position = 1.18
    return min(1.0, (saturation * 0.46 + value_std * 0.34 + edge * 0.20) * position)


def _bounded_square_crop(image: Image.Image, x1: int, y1: int, side: int) -> Image.Image | None:
    w, h = image.size
    if side < 32 or side > min(w, h):
        return None
    x1 = max(0, min(w - side, x1))
    y1 = max(0, min(h - side, y1))
    return image.crop((x1, y1, x1 + side, y1 + side))


def _square_crops(image: Image.Image, side: int) -> Iterable[Image.Image]:
    w, h = image.size
    if w == h:
        yield image
        return
    if w > h:
        xs = [0, (w - side) // 2, w - side]
        for x in sorted(set(xs)):
            yield image.crop((x, 0, x + side, side))
    else:
        ys = [0, (h - side) // 2, h - side]
        for y in sorted(set(ys)):
            yield image.crop((0, y, side, y + side))


def _trim_border(image: Image.Image) -> Image.Image:
    bg = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, bg)
    bbox = diff.getbbox()
    if not bbox:
        return image
    w, h = image.size
    x1, y1, x2, y2 = bbox
    if (x2 - x1) < w * 0.35 or (y2 - y1) < h * 0.35:
        return image
    return image.crop(bbox)


def _pil_to_cv2(pil_image: Image.Image):
    if cv2 is None or np is None:
        return None
    rgb = pil_image.convert("RGB")
    return cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)


def _open_cover(path: str) -> Image.Image | None:
    if not os.path.exists(path):
        return None
    try:
        with Image.open(path) as img:
            return img.convert("RGB")
    except Exception:
        return None


def _file_mtime(path: str) -> float | None:
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _normalize_cover_name(value: Any) -> str:
    if not value:
        return ""
    name = os.path.basename(str(value).strip())
    return name if name.lower().endswith(".png") else f"{name}.png"


def _dedupe_song_results(results: list[ImageRecognitionResult]) -> list[ImageRecognitionResult]:
    deduped = []
    seen = set()
    for item in results:
        song_id = item.song.get("id") or item.cover_name
        if song_id in seen:
            continue
        seen.add(song_id)
        deduped.append(item)
    return deduped
