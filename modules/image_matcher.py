"""
图片相似度匹配模块 - 旧版混合策略恢复版。

核心沿用历史实现：
1. pHash + LSH 快速匹配完整曲绘。
2. SIFT + FLANN + RANSAC 几何验证匹配场景照片、小曲绘、部分截图。
"""
from __future__ import annotations

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import cv2
import imagehash
import numpy as np
from PIL import Image, ImageOps

from modules.config_loader import COVERS_DIR
from modules.image_cache import get_cover_image


logger = logging.getLogger(__name__)

HASH_THRESHOLD = 15
DOWNLOAD_WORKERS = 12

_cache_lock = threading.RLock()
_cache_signature = None
_hash_cache = {}
_feature_cache = {}
_lsh_index = {}


@dataclass(frozen=True)
class ImageRecognitionResult:
    song: dict[str, Any]
    cover_name: str
    score: float
    method: str
    hash_score: float
    verify_score: float


def pil_to_cv2(pil_image):
    """将 PIL Image 转换为 OpenCV 格式。"""
    pil_image = ImageOps.exif_transpose(pil_image)
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


def calculate_image_hash(pil_image):
    """计算感知哈希，沿用旧版 hash_size=16。"""
    try:
        pil_image = ImageOps.exif_transpose(pil_image)
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        return imagehash.phash(pil_image, hash_size=16)
    except Exception as e:
        logger.error("[ImageMatcher] 计算哈希失败: %s", e)
        return None


def extract_sift_features(image_cv2):
    """提取 SIFT 特征点。"""
    try:
        gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
        sift = cv2.SIFT_create(nfeatures=1500)
        keypoints, descriptors = sift.detectAndCompute(gray, None)
        if descriptors is None or len(keypoints) < 15:
            return None, None
        return keypoints, descriptors
    except Exception as e:
        logger.debug("[ImageMatcher] SIFT 特征提取失败: %s", e)
        return None, None


def match_sift_features(kp1, desc1, kp2, desc2):
    """匹配 SIFT 特征点，返回 good 数、RANSAC 几何验证数、验证通过率。"""
    try:
        if desc1 is None or desc2 is None:
            return 0, 0, 0.0

        flann = cv2.FlannBasedMatcher(
            dict(algorithm=1, trees=5),
            dict(checks=50),
        )
        matches = flann.knnMatch(desc1, desc2, k=2)

        good_matches = []
        for pair in matches:
            if len(pair) == 2:
                m, n = pair
                if m.distance < 0.65 * n.distance:
                    good_matches.append(m)

        if len(good_matches) < 8:
            return len(good_matches), 0, 0.0

        try:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 3.0)
            if mask is not None:
                geometric_matches = int(np.sum(mask))
                geometric_ratio = geometric_matches / len(good_matches)
                return len(good_matches), geometric_matches, geometric_ratio
        except Exception:
            pass

        return len(good_matches), 0, 0.0
    except Exception as e:
        logger.debug("[ImageMatcher] 特征匹配失败: %s", e)
        return 0, 0, 0.0


def warm_image_recognition_index(songs_data: list[dict[str, Any]], covers_dir: str | None = None) -> int:
    """预热曲绘识别缓存，返回可用曲绘数量。"""
    return load_cover_cache(covers_dir or COVERS_DIR, songs_data)


def recognize_songs_from_image(
    input_image: Image.Image,
    songs_data: list[dict[str, Any]],
    covers_dir: str | None = None,
    max_results: int = 3,
) -> list[ImageRecognitionResult]:
    """当前 main 使用的识别入口。"""
    matches = find_similar_cover(
        input_image,
        covers_dir=covers_dir,
        songs_data=songs_data,
        hash_threshold=HASH_THRESHOLD,
        return_multiple=True,
        max_results=max_results,
    )
    if not matches:
        return []

    results = []
    for cover_name, score, method in matches:
        songs = _find_songs_by_cover_name(cover_name, songs_data, method)
        for song in songs:
            normalized_score = _normalize_score(score, method)
            results.append(ImageRecognitionResult(
                song=song,
                cover_name=_normalize_cover_name(cover_name),
                score=normalized_score,
                method=method,
                hash_score=normalized_score if method == "hash" else 0.0,
                verify_score=normalized_score if method == "sift" else 0.0,
            ))

    results.sort(key=lambda item: item.score, reverse=True)
    return _dedupe_song_results(results)[:max_results]


def find_song_by_cover(
    input_image,
    songs_data,
    covers_dir=None,
    hash_threshold=HASH_THRESHOLD,
    return_multiple=False,
    max_results=3,
):
    """兼容旧接口。"""
    result = find_similar_cover(
        input_image,
        covers_dir=covers_dir,
        songs_data=songs_data,
        hash_threshold=hash_threshold,
        return_multiple=return_multiple,
        max_results=max_results,
    )

    if return_multiple:
        songs = []
        for cover_name, _, method in result:
            songs.extend(_find_songs_by_cover_name(cover_name, songs_data, method))
        return songs[:max_results]

    cover_name, _, method = result
    if cover_name is None:
        return None
    songs = _find_songs_by_cover_name(cover_name, songs_data, method)
    return songs[0] if songs else None


def find_similar_cover(
    input_image,
    covers_dir=None,
    songs_data=None,
    hash_threshold=HASH_THRESHOLD,
    return_multiple=False,
    max_results=3,
):
    """旧版混合策略：哈希优先，失败后全库 SIFT。"""
    covers_dir = covers_dir or COVERS_DIR
    if not os.path.exists(covers_dir):
        logger.warning("[ImageMatcher] 封面目录不存在: %s", covers_dir)
        return [] if return_multiple else (None, None, None)

    load_cover_cache(covers_dir, songs_data)

    logger.info("[ImageMatcher] 开始图片识别（旧版混合策略）")

    input_hash = calculate_image_hash(input_image)
    if input_hash:
        hash_matches = _hash_match(input_hash, hash_threshold)
        if hash_matches:
            logger.info("[ImageMatcher] 哈希匹配成功: %s", len(hash_matches))
            if return_multiple:
                return [
                    (item["cover_name"], item["confidence"], "hash")
                    for item in hash_matches[:max_results]
                ]
            best = hash_matches[0]
            return best["cover_name"], best["confidence"], "hash"

    feature_matches = _sift_match(input_image)
    if feature_matches:
        logger.info("[ImageMatcher] SIFT 匹配成功: %s", len(feature_matches))
        if return_multiple:
            return [
                (item["cover_name"], item["score"], "sift")
                for item in feature_matches[:max_results]
            ]
        best = feature_matches[0]
        return best["cover_name"], best["score"], "sift"

    logger.warning("[ImageMatcher] 未找到匹配曲绘")
    return [] if return_multiple else (None, None, None)


def load_cover_cache(covers_dir, songs_data=None):
    """预加载曲绘哈希、SIFT 特征和 LSH 索引。"""
    global _cache_signature, _hash_cache, _feature_cache, _lsh_index

    rows = _cover_rows_from_songs(songs_data) if songs_data else None
    signature = _cover_cache_signature(covers_dir, rows)

    with _cache_lock:
        if _cache_signature == signature:
            return len(_hash_cache)

        logger.info("[ImageMatcher] 正在加载封面数据库...")
        _hash_cache = {}
        _feature_cache = {}
        _lsh_index = {}

        cover_files = _ensure_cover_files(covers_dir, rows)
        loaded = 0
        for cover_file in cover_files:
            try:
                cover_path = os.path.join(covers_dir, cover_file)
                cover_name = cover_file.replace(".png", "")

                pil_img = Image.open(cover_path)
                cv2_img = cv2.imread(cover_path)
                if cv2_img is None:
                    continue

                phash = calculate_image_hash(pil_img)
                if phash:
                    _hash_cache[cover_name] = phash

                kp, desc = extract_sift_features(cv2_img)
                if desc is not None:
                    _feature_cache[cover_name] = (kp, desc)

                loaded += 1
            except Exception as e:
                logger.debug("[ImageMatcher] 加载封面失败: file=%s error=%s", cover_file, e)

        _build_lsh_index()
        _cache_signature = signature
        logger.info(
            "[ImageMatcher] 封面数据库加载完成: loaded=%s hash=%s feature=%s",
            loaded, len(_hash_cache), len(_feature_cache),
        )
        return len(_hash_cache)


def _ensure_cover_files(covers_dir, rows):
    os.makedirs(covers_dir, exist_ok=True)
    if not rows:
        return [f for f in os.listdir(covers_dir) if f.endswith(".png")]

    existing = set(os.listdir(covers_dir))
    missing = [row for row in rows if row["cover_name"] not in existing and row.get("cover_url")]

    if missing:
        logger.info("[ImageMatcher] 下载缺失曲绘: %s", len(missing))
        with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
            futures = [
                executor.submit(get_cover_image, row["cover_url"], row["cover_name"])
                for row in missing
            ]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.debug("[ImageMatcher] 曲绘下载任务失败: %s", e)

    return [row["cover_name"] for row in rows if os.path.exists(os.path.join(covers_dir, row["cover_name"]))]


def _hash_match(input_hash, hash_threshold):
    bucket_keys = _hash_to_lsh_bucket(input_hash)
    candidates = set()
    for bucket_key in bucket_keys:
        candidates.update(_lsh_index.get(bucket_key, []))

    logger.info(
        "[ImageMatcher] LSH 候选集: %s/%s",
        len(candidates), len(_hash_cache),
    )

    hash_matches = []
    for cover_name in candidates:
        cover_hash = _hash_cache.get(cover_name)
        if cover_hash is None:
            continue
        distance = abs(input_hash - cover_hash)
        if distance <= hash_threshold:
            confidence = 100 * (1 - distance / (hash_threshold * 2))
            hash_matches.append({
                "cover_name": cover_name,
                "distance": distance,
                "confidence": confidence,
            })

    hash_matches.sort(key=lambda item: item["distance"])
    return hash_matches


def _sift_match(input_image):
    input_cv2 = pil_to_cv2(input_image)
    input_kp, input_desc = extract_sift_features(input_cv2)
    if input_desc is None:
        logger.warning("[ImageMatcher] 输入图片特征点不足")
        return []

    logger.info("[ImageMatcher] 输入图片特征点: %s", len(input_kp))
    feature_matches = []
    for cover_name, (cover_kp, cover_desc) in _feature_cache.items():
        good_matches, geometric_matches, match_quality = match_sift_features(
            input_kp, input_desc,
            cover_kp, cover_desc,
        )
        if match_quality < 0.75 or geometric_matches < 8:
            continue

        coverage = geometric_matches / len(cover_kp) if cover_kp else 0
        score = (match_quality ** 2) * geometric_matches * (1 + coverage)
        feature_matches.append({
            "cover_name": cover_name,
            "score": score,
            "geometric_matches": geometric_matches,
            "match_quality": match_quality,
            "coverage": coverage,
        })

    feature_matches.sort(key=lambda item: item["score"], reverse=True)
    return feature_matches


def _hash_to_lsh_bucket(hash_value, num_bands=32, band_size=8):
    """旧版 LSH：16x16 pHash 拆成 32 个 8-bit band。"""
    hash_array = hash_value.hash.flatten()
    bucket_keys = []
    for band_id in range(num_bands):
        start = band_id * band_size
        end = min(start + band_size, len(hash_array))
        band_bits = hash_array[start:end]
        bucket_key = (band_id, int("".join(map(str, band_bits.astype(int))), 2))
        bucket_keys.append(bucket_key)
    return bucket_keys


def _build_lsh_index():
    logger.info("[ImageMatcher] 正在构建 LSH 索引...")
    _lsh_index.clear()
    for cover_name, cover_hash in _hash_cache.items():
        for bucket_key in _hash_to_lsh_bucket(cover_hash):
            _lsh_index.setdefault(bucket_key, []).append(cover_name)
    logger.info("[ImageMatcher] LSH 索引构建完成: buckets=%s", len(_lsh_index))


def _cover_rows_from_songs(songs_data):
    rows = {}
    for song in songs_data or []:
        cover_name = _normalize_cover_name(song.get("cover_name"))
        if not cover_name:
            continue
        rows.setdefault(cover_name, {
            "cover_name": cover_name,
            "cover_url": song.get("cover_url") or "",
        })
    return list(rows.values())


def _cover_cache_signature(covers_dir, rows):
    if rows:
        names = ",".join(sorted(row["cover_name"] for row in rows))
        return f"{os.path.abspath(covers_dir)}:{len(rows)}:{hash(names)}"
    try:
        stat = os.stat(covers_dir)
        count = len([f for f in os.listdir(covers_dir) if f.endswith(".png")])
        return f"{os.path.abspath(covers_dir)}:{count}:{stat.st_mtime}"
    except OSError:
        return f"{os.path.abspath(covers_dir)}:missing"


def _find_songs_by_cover_name(cover_name, songs_data, method):
    target_cover_with_ext = _normalize_cover_name(cover_name)
    target_cover_without_ext = target_cover_with_ext.replace(".png", "")
    result = []
    for song in songs_data:
        song_cover = song.get("cover_name", "")
        if song_cover == target_cover_with_ext or song_cover == target_cover_without_ext:
            logger.info(
                "[ImageMatcher] 识别歌曲: title=%s artist=%s method=%s",
                song.get("title"), song.get("artist"), method,
            )
            result.append(song)
    return result


def _normalize_cover_name(value):
    if not value:
        return ""
    name = os.path.basename(str(value).strip())
    return name if name.lower().endswith(".png") else f"{name}.png"


def _normalize_score(score, method):
    if method == "hash":
        return round(float(score) / 100, 4)
    return round(min(1.0, float(score) / 35), 4)


def _dedupe_song_results(results):
    deduped = []
    seen = set()
    for item in results:
        key = item.song.get("id") or item.cover_name
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
