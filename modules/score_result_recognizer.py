"""
maimai result-photo OCR integration.

This module wraps the standalone scripts under scripts/ so main.py can call the
recognizer without importing CLI code directly.
"""
from __future__ import annotations

import math
import logging
import re
import unicodedata
import difflib
import sys
import threading
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw
from PIL import UnidentifiedImageError

from modules.config_loader import read_dxdata
from modules.maimai_manager import (
    calc_judgement_achievement_range,
    calc_score,
    get_note_score,
)
from modules.song_matcher import find_matching_songs, normalize_text


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

_TITLE_OCR_CONFUSABLES = str.maketrans({
    "极": "極",
    "圈": "圏",
    "園": "圏",
})


def _normalize_title_for_ocr(text):
    return normalize_text(str(text or "")).translate(_TITLE_OCR_CONFUSABLES)


def _rolling_title_parts(title):
    parts = []
    for part in re.split(r"\s+", str(title or "").strip()):
        normalized = _normalize_title_for_ocr(part)
        if len(normalized) >= 2:
            parts.append(normalized)
    return parts


def _rotated_title_candidates(parts):
    if len(parts) < 2:
        return []
    candidates = []
    seen = set()
    for index in range(1, len(parts)):
        rotated = parts[index:] + parts[:index]
        joined = "".join(rotated)
        if len(joined) < 4 or joined in seen:
            continue
        seen.add(joined)
        candidates.append((rotated, joined))
    return candidates


def _song_matches_rolling_title(normalized_song_title, rotated_parts):
    if len(rotated_parts) < 2 or len(normalized_song_title) < 4:
        return False

    first = rotated_parts[0]
    last = rotated_parts[-1]
    if not normalized_song_title.startswith(first) or not normalized_song_title.endswith(last):
        return False

    cursor = 0
    for part in rotated_parts:
        position = normalized_song_title.find(part, cursor)
        if position < 0:
            return False
        cursor = position + len(part)
    return True


def _title_edit_similarity(left, right):
    if not left or not right:
        return 0.0
    return difflib.SequenceMatcher(None, left, right).ratio()


def _edit_distance_at_most_one(left, right):
    if abs(len(left) - len(right)) > 1:
        return False
    if left == right:
        return True
    if len(left) == len(right):
        return sum(a != b for a, b in zip(left, right)) <= 1

    shorter, longer = (left, right) if len(left) < len(right) else (right, left)
    index_short = 0
    skipped = 0
    for character in longer:
        if index_short < len(shorter) and shorter[index_short] == character:
            index_short += 1
            continue
        skipped += 1
        if skipped > 1:
            return False
    return True


def _title_edge_trim_similarity(normalized_ocr, normalized_song_title):
    """Score cases where OCR adds or drops a leading/trailing character."""
    candidates = [normalized_ocr]
    if len(normalized_ocr) >= 5:
        candidates.extend([
            normalized_ocr[1:],
            normalized_ocr[:-1],
        ])
    if len(normalized_ocr) >= 6:
        candidates.extend([
            normalized_ocr[1:-1],
            normalized_ocr[2:],
            normalized_ocr[:-2],
        ])
    return max(
        _title_edit_similarity(candidate, normalized_song_title)
        for candidate in candidates
        if candidate
    )


def _cyclic_title_similarity(normalized_ocr, normalized_song_title):
    """Score scrolling-title crops such as tail+head without whitespace."""
    if len(normalized_ocr) < 4 or len(normalized_song_title) < 4:
        return 0.0

    doubled_title = normalized_song_title + normalized_song_title
    if normalized_ocr in doubled_title:
        coverage = len(normalized_ocr) / max(1, len(normalized_song_title))
        return min(0.97, 0.72 + coverage * 0.25)

    best = 0.0
    # Compare OCR against the visible prefix of every circular rotation. This
    # catches one-character OCR noise inside a wrapped title crop.
    for index in range(len(normalized_song_title)):
        rotated = normalized_song_title[index:] + normalized_song_title[:index]
        window = rotated[:len(normalized_ocr)]
        if len(window) >= 4:
            best = max(best, _title_edit_similarity(normalized_ocr, window))
        if len(normalized_ocr) > len(rotated):
            best = max(best, _title_edit_similarity(normalized_ocr, rotated))
    return best


def _dedupe_title_matches(ranked_matches, max_results):
    seen = set()
    matches = []
    match_kinds = []
    for rank in sorted(
        ranked_matches,
        key=lambda item: (
            item[0],
            item[1],
            item[2],
            str(item[-1]),
            str(item[-2].get("id") or ""),
            str(item[-2].get("type") or ""),
        ),
    ):
        song = rank[-2]
        match_kind = rank[-1]
        song_key = (
            str(song.get("id") or ""),
            str(song.get("type") or ""),
            normalize_text(str(song.get("title") or "")),
        )
        if song_key in seen:
            continue
        seen.add(song_key)
        matches.append(song)
        match_kinds.append(match_kind)
        if len(matches) >= max_results:
            break
    return matches, match_kinds


def _song_identity_key(song):
    return (
        str(song.get("id") or ""),
        str(song.get("type") or ""),
        normalize_text(str(song.get("title") or "")),
    )


def _match_recognized_song_title(title, songs, max_results=12):
    """Match noisy OCR text while preferring complete canonical song titles."""
    normalized_exact_ocr = normalize_text(str(title or ""))
    normalized_ocr = _normalize_title_for_ocr(title)
    if not normalized_exact_ocr:
        return [], "none"

    exact_matches = [
        song for song in songs
        if normalize_text(str(song.get("title") or "")) == normalized_exact_ocr
    ]
    if exact_matches:
        return exact_matches[:max_results], "exact"

    if normalized_ocr != normalized_exact_ocr:
        confusable_matches = [
            song for song in songs
            if _normalize_title_for_ocr(song.get("title")) == normalized_ocr
        ]
        if confusable_matches:
            return confusable_matches[:max_results], "ocr_confusable"

    rolling_candidates = _rotated_title_candidates(_rolling_title_parts(title))
    if rolling_candidates:
        for _, candidate in rolling_candidates:
            rolling_exact_matches = [
                song for song in songs
                if _normalize_title_for_ocr(song.get("title")) == candidate
            ]
            if rolling_exact_matches:
                return rolling_exact_matches[:max_results], "rolling_exact"

        rolling_partial_matches = []
        matched_song_ids = set()
        for parts, candidate in rolling_candidates:
            for song in songs:
                normalized_song_title = _normalize_title_for_ocr(song.get("title"))
                if _song_matches_rolling_title(normalized_song_title, parts):
                    song_key = song.get("id") or normalized_song_title
                    if song_key in matched_song_ids:
                        continue
                    matched_song_ids.add(song_key)
                    rolling_partial_matches.append((len(candidate), song))
        if rolling_partial_matches:
            longest_length = max(length for length, _ in rolling_partial_matches)
            longest_matches = [
                song for length, song in rolling_partial_matches
                if length == longest_length
            ]
            return longest_matches[:max_results], "rolling_partial"

    def normalize_ocr_kana(value):
        normalized = normalize_text(str(value or ""))
        return "".join(
            character
            for character in unicodedata.normalize("NFD", normalized)
            if character not in {"\u3099", "\u309a"}
        )

    # Japanese OCR often confuses voiced and semi-voiced kana, for example
    # ぱ/ば. Ignore dakuten only when that produces one canonical song title.
    normalized_kana_ocr = normalize_ocr_kana(title)
    if len(normalized_kana_ocr) >= 4:
        kana_matches = [
            song for song in songs
            if normalize_ocr_kana(song.get("title")) == normalized_kana_ocr
        ]
        canonical_titles = {
            normalize_text(str(song.get("title") or ""))
            for song in kana_matches
        }
        if kana_matches and len(canonical_titles) == 1:
            return kana_matches[:max_results], "ocr_kana"

    directional_matches = []
    for song in songs:
        normalized_song_title = _normalize_title_for_ocr(song.get("title"))
        if len(normalized_song_title) < 2:
            continue

        score = None
        match_kind = None
        # OCR may read only the visible prefix of a scrolling long title:
        # "AAABBBCCC" can appear as "CCC AAA" or be cut as "AAABBB".
        if len(normalized_ocr) >= 4 and normalized_song_title.startswith(normalized_ocr):
            score = len(normalized_ocr) / max(1, len(normalized_song_title))
            match_kind = "prefix"
        elif len(normalized_song_title) >= 4 and normalized_song_title in normalized_ocr:
            score = len(normalized_song_title) / max(1, len(normalized_ocr))
            match_kind = "embedded"
        elif (
            min(len(normalized_ocr), len(normalized_song_title)) >= 4
            and _edit_distance_at_most_one(normalized_ocr, normalized_song_title)
        ):
            score = 0.93
            match_kind = "edit_fuzzy"
        elif len(normalized_ocr) >= 6:
            similarity = difflib.SequenceMatcher(
                None,
                normalized_ocr,
                normalized_song_title,
            ).ratio()
            if similarity >= 0.76:
                score = similarity
                match_kind = "fuzzy"

        cyclic_score = _cyclic_title_similarity(normalized_ocr, normalized_song_title)
        if cyclic_score >= 0.72 and cyclic_score > (score or 0):
            score = cyclic_score
            match_kind = "rolling_fuzzy"

        trim_score = _title_edge_trim_similarity(normalized_ocr, normalized_song_title)
        if trim_score >= 0.88 and trim_score > (score or 0):
            score = trim_score
            match_kind = "edge_fuzzy"

        if score is not None:
            directional_matches.append((
                (
                    0 if match_kind == "edge_fuzzy"
                    else 1 if match_kind == "rolling_fuzzy"
                    else 2 if match_kind == "edit_fuzzy"
                    else 3 if match_kind == "prefix"
                    else 4 if match_kind == "embedded"
                    else 5
                ),
                -score,
                -len(normalized_song_title),
                song,
                match_kind,
            ))
    if directional_matches:
        matches, match_kinds = _dedupe_title_matches(directional_matches, max_results)
        match_types = set(match_kinds)
        if match_types == {"embedded"}:
            longest_length = max(
                len(normalize_text(str(song.get("title") or "")))
                for song in matches
            )
            extra_length = len(normalized_ocr) - longest_length
            match_type = "ocr_embedded" if extra_length <= 2 else "embedded"
        elif "edge_fuzzy" in match_types:
            match_type = "edge_fuzzy"
        elif "rolling_fuzzy" in match_types:
            match_type = "rolling_fuzzy"
        elif "edit_fuzzy" in match_types:
            match_type = "edit_fuzzy"
        elif "prefix" in match_types:
            match_type = "prefix"
        else:
            match_type = "fuzzy"
        return matches, match_type

    return (
        find_matching_songs(title, songs, max_results=max_results, threshold=0.82),
        "fuzzy",
    )


def _calc_achievement_distance(achievement, score_range, tolerance=0.0006):
    if not isinstance(achievement, (int, float)) or not score_range:
        return None
    minimum = float(score_range["minimum"])
    maximum = float(score_range["maximum"])
    if minimum - tolerance <= achievement <= maximum + tolerance:
        return 0.0
    return min(abs(achievement - minimum), abs(achievement - maximum))


def _find_calc_judgement_uncertainties(notes, judgement, achievement):
    """Find single OCR cells that could explain a Calc score mismatch."""
    if not isinstance(achievement, (int, float)):
        return []

    row_names = ("tap", "hold", "slide", "touch", "break")
    value_names = ("critical_perfect", "perfect", "great", "good")
    uncertainties = []
    for row_name in row_names:
        source_row = judgement.get(row_name)
        row_missing = not isinstance(source_row, dict)
        if row_missing:
            source_row = {
                "critical_perfect": 0,
                "perfect": 0,
                "great": 0,
                "good": 0,
                "miss": 0,
            }
        try:
            expected = max(0, int(notes.get(row_name, 0)))
        except (TypeError, ValueError):
            continue
        if expected <= 0:
            continue
        if row_missing:
            uncertainties.append({
                "row": row_name,
                "field": "row",
                "ocr": None,
                "candidate_min": None,
                "candidate_max": None,
                "candidate_count": 0,
                "miss_min": None,
                "miss_max": None,
                "row_missing": True,
            })
            continue

        for value_name in value_names:
            try:
                ocr_value = max(0, int(source_row.get(value_name, 0)))
            except (TypeError, ValueError):
                continue
            candidates = []
            for candidate_value in range(expected + 1):
                if candidate_value == ocr_value:
                    continue
                candidate_row = dict(source_row)
                candidate_row[value_name] = candidate_value
                known = sum(max(0, int(candidate_row.get(name, 0))) for name in value_names)
                candidate_miss = expected - known
                if candidate_miss < 0:
                    continue
                candidate_row["miss"] = candidate_miss
                candidate_judgement = dict(judgement)
                candidate_judgement[row_name] = candidate_row
                score_range = calc_judgement_achievement_range(notes, candidate_judgement)
                if _calc_achievement_distance(achievement, score_range) == 0:
                    candidates.append((candidate_value, candidate_miss))

            if not candidates:
                continue
            values = sorted({value for value, _ in candidates})
            misses = sorted({miss for _, miss in candidates})
            uncertainties.append({
                "row": row_name,
                "field": value_name,
                "ocr": ocr_value,
                "candidate_min": values[0],
                "candidate_max": values[-1],
                "candidate_count": len(values),
                "miss_min": misses[0],
                "miss_max": misses[-1],
                "row_missing": row_missing,
            })
    return uncertainties


def _apply_unique_calc_judgement_correction(
    notes,
    judgement,
    achievement,
    uncertainties,
):
    """Apply a Calc correction only when one cell has one valid solution."""
    def row_total_matches_notes(row_name):
        row = judgement.get(row_name)
        if not isinstance(row, dict):
            return False
        try:
            expected = max(0, int(notes.get(row_name, 0) or 0))
            total = sum(
                max(0, int(row.get(field_name, 0) or 0))
                for field_name in (
                    "critical_perfect",
                    "perfect",
                    "great",
                    "good",
                    "miss",
                )
            )
        except (TypeError, ValueError):
            return False
        return expected > 0 and total == expected

    resolvable = [
        item for item in uncertainties
        if not item.get("row_missing")
        and item.get("candidate_count") == 1
        and item.get("candidate_min") == item.get("candidate_max")
        and item.get("miss_min") == item.get("miss_max")
        and not row_total_matches_notes(item.get("row"))
    ]
    if len(resolvable) == 1:
        uncertainty = resolvable[0]
    else:
        break_non_cp = [
            item for item in resolvable
            if item.get("row") == "break"
            and item.get("field") in {"perfect", "great", "good"}
        ]
        if len(break_non_cp) != 1:
            return None
        uncertainty = break_non_cp[0]

    row_name = uncertainty.get("row")
    field_name = uncertainty.get("field")
    if field_name not in {"critical_perfect", "perfect", "great", "good"}:
        return None
    source_row = judgement.get(row_name)
    if not isinstance(source_row, dict):
        return None

    corrected_row = dict(source_row)
    previous_value = max(0, int(corrected_row.get(field_name, 0)))
    previous_miss = max(0, int(corrected_row.get("miss", 0)))
    corrected_row[field_name] = uncertainty["candidate_min"]
    corrected_row["miss"] = uncertainty["miss_min"]
    corrected_judgement = dict(judgement)
    corrected_judgement[row_name] = corrected_row
    score_range = calc_judgement_achievement_range(notes, corrected_judgement)
    if _calc_achievement_distance(achievement, score_range) != 0:
        return None
    if not _has_break_calc_solution(notes, corrected_judgement, achievement):
        return None

    return {
        "judgement": corrected_judgement,
        "score_range": score_range,
        "correction": {
            "row": row_name,
            "field": field_name,
            "ocr": previous_value,
            "validated": uncertainty["candidate_min"],
            "miss_ocr": previous_miss,
            "miss_validated": uncertainty["miss_min"],
        },
    }


def _apply_calc_row_balance(
    notes,
    judgement,
    achievement,
    uncertainties,
):
    """Balance CP and MISS when Calc isolates OCR errors to one normal row."""
    if not isinstance(achievement, (int, float)):
        return None
    suspected_rows = {
        item.get("row")
        for item in uncertainties
        if item.get("row") in {"tap", "hold", "slide", "touch"}
        and not item.get("row_missing")
    }
    if len(suspected_rows) != 1:
        return None

    row_name = next(iter(suspected_rows))
    source_row = judgement.get(row_name)
    if not isinstance(source_row, dict):
        return None
    try:
        expected = max(0, int(notes.get(row_name, 0)))
        previous_cp = max(0, int(source_row.get("critical_perfect", 0)))
        previous_miss = max(0, int(source_row.get("miss", 0)))
        perfect = max(0, int(source_row.get("perfect", 0)))
        great = max(0, int(source_row.get("great", 0)))
        good = max(0, int(source_row.get("good", 0)))
    except (TypeError, ValueError):
        return None

    row_total = previous_cp + perfect + great + good + previous_miss
    if row_total == expected:
        return None

    remaining = expected - perfect - great - good
    if remaining < 0:
        return None

    candidates = []
    for candidate_miss in range(remaining + 1):
        candidate_cp = remaining - candidate_miss
        if candidate_cp == previous_cp and candidate_miss == previous_miss:
            continue
        candidate_row = dict(source_row)
        candidate_row["critical_perfect"] = candidate_cp
        candidate_row["miss"] = candidate_miss
        candidate_judgement = dict(judgement)
        candidate_judgement[row_name] = candidate_row
        score_range = calc_judgement_achievement_range(
            notes,
            candidate_judgement,
        )
        if _calc_achievement_distance(achievement, score_range) != 0:
            continue
        if not _has_break_calc_solution(notes, candidate_judgement, achievement):
            continue
        candidates.append({
            "judgement": candidate_judgement,
            "score_range": score_range,
            "candidate_cp": candidate_cp,
            "candidate_miss": candidate_miss,
        })

    if len(candidates) != 1:
        return None
    candidate = candidates[0]
    return {
        "judgement": candidate["judgement"],
        "score_range": candidate["score_range"],
        "correction": {
            "row": row_name,
            "field": "critical_perfect",
            "ocr": previous_cp,
            "validated": candidate["candidate_cp"],
            "miss_ocr": previous_miss,
            "miss_validated": candidate["candidate_miss"],
        },
    }


def _apply_same_row_miss_redistribution(
    notes,
    judgement,
    achievement,
    uncertainties,
):
    """Redistribute same-row MISS OCR noise without changing row totals."""
    if not isinstance(achievement, (int, float)):
        return None

    uncertain_targets = {
        (item.get("row"), item.get("field"))
        for item in uncertainties
        if not item.get("row_missing")
    }
    exact_uncertainties = {
        (item.get("row"), item.get("field")): item
        for item in uncertainties
        if not item.get("row_missing")
        and item.get("candidate_count") == 1
        and item.get("candidate_min") == item.get("candidate_max")
        and item.get("miss_min") == item.get("miss_max")
    }
    target_fields = ("great", "good", "perfect", "critical_perfect")
    field_names = (
        "critical_perfect",
        "perfect",
        "great",
        "good",
        "miss",
    )
    current_range = calc_judgement_achievement_range(notes, judgement)
    current_distance = _calc_achievement_distance(achievement, current_range)
    if current_distance is None or current_distance == 0:
        return None

    def iter_distributions(total, slot_count):
        if slot_count <= 0:
            return
        if slot_count == 1:
            yield (total,)
            return
        for value in range(total + 1):
            for rest in iter_distributions(total - value, slot_count - 1):
                yield (value, *rest)

    candidates = []
    for row_name in ("tap", "hold", "slide", "touch"):
        source_row = judgement.get(row_name)
        if not isinstance(source_row, dict):
            continue
        try:
            expected = max(0, int(notes.get(row_name, 0) or 0))
            original = {
                field_name: max(0, int(source_row.get(field_name, 0) or 0))
                for field_name in field_names
            }
        except (TypeError, ValueError):
            continue
        if expected <= 0 or sum(original.values()) != expected:
            continue
        miss = original["miss"]
        if miss <= 0:
            continue

        eligible_targets = [
            field_name for field_name in target_fields
            if (
                original[field_name] == 0
                or (row_name, field_name) in uncertain_targets
            )
        ]
        if not eligible_targets:
            continue

        checked_count = 0
        for amount in range(1, miss + 1):
            for distribution in iter_distributions(amount, len(eligible_targets)):
                if not any(distribution):
                    continue
                checked_count += 1
                if checked_count > 250_000:
                    break
                candidate_row = dict(original)
                candidate_row["miss"] -= amount
                changed_targets = []
                for target_field, increment in zip(eligible_targets, distribution):
                    if increment <= 0:
                        continue
                    candidate_row[target_field] += increment
                    changed_targets.append({
                        "field": target_field,
                        "amount": increment,
                        "before": original[target_field],
                        "after": candidate_row[target_field],
                    })
                if not changed_targets:
                    continue
                candidate_judgement = dict(judgement)
                candidate_judgement[row_name] = candidate_row
                score_range = calc_judgement_achievement_range(
                    notes,
                    candidate_judgement,
                )
                distance = _calc_achievement_distance(achievement, score_range)
                if distance is None or distance >= current_distance:
                    continue
                if distance != 0:
                    continue
                has_break_solution = _has_break_calc_solution(
                    notes,
                    candidate_judgement,
                    achievement,
                )
                row_exact_uncertainties = {
                    field: item
                    for (uncertain_row, field), item in exact_uncertainties.items()
                    if uncertain_row == row_name
                }
                exact_hits = sum(
                    1
                    for field, item in row_exact_uncertainties.items()
                    if candidate_row.get(field) == item.get("candidate_min")
                    and candidate_row.get("miss") == item.get("miss_min")
                )
                exact_misses = len(row_exact_uncertainties) - exact_hits
                changed_non_uncertain_zero_targets = sum(
                    1
                    for item in changed_targets
                    if original[item["field"]] == 0
                    and (row_name, item["field"]) not in exact_uncertainties
                )
                candidates.append({
                    "judgement": candidate_judgement,
                    "score_range": score_range,
                    "row": row_name,
                    "amount": amount,
                    "changed_targets": changed_targets,
                    "miss_before": miss,
                    "miss_after": candidate_row["miss"],
                    "rank": (
                        0 if has_break_solution else 1,
                        exact_misses,
                        -exact_hits,
                        changed_non_uncertain_zero_targets,
                        len(changed_targets),
                        amount,
                        tuple(
                            target_fields.index(item["field"])
                            for item in changed_targets
                        ),
                        sum(
                            abs(candidate_row[name] - original[name])
                            for name in field_names
                        ),
                    ),
                })
            if checked_count > 250_000:
                break

    if not candidates:
        return None

    candidates.sort(key=lambda item: item["rank"])
    best = candidates[0]
    if len(candidates) > 1:
        second = candidates[1]
        if second["rank"] == best["rank"]:
            return None

    row_name = best["row"]
    corrections = [
        {
            "row": row_name,
            "field": "miss",
            "ocr": best["miss_before"],
            "validated": best["miss_after"],
            "miss_ocr": best["miss_before"],
            "miss_validated": best["miss_after"],
            "same_row_miss_redistribution": True,
        },
    ]
    for target in best["changed_targets"]:
        corrections.append({
            "row": row_name,
            "field": target["field"],
            "ocr": target["before"],
            "validated": target["after"],
            "miss_ocr": best["miss_before"],
            "miss_validated": best["miss_after"],
            "same_row_miss_redistribution": True,
        })
    return {
        "judgement": best["judgement"],
        "score_range": best["score_range"],
        "correction": corrections[0],
        "corrections": corrections,
    }


def _has_break_calc_solution(notes, judgement, achievement):
    """Return whether the current table can resolve BREAK detail with Calc."""
    if not isinstance(achievement, (int, float)):
        return True
    try:
        break_count = max(0, int(notes.get("break", 0) or 0))
    except (TypeError, ValueError):
        return False
    if break_count <= 0:
        return True
    break_row = judgement.get("break")
    if isinstance(break_row, dict):
        return _infer_break_judgement_detail(notes, judgement, achievement) is not None
    return _infer_missing_break_judgement(notes, judgement, achievement) is not None


def _infer_missing_break_judgement(notes, judgement, achievement):
    """Infer a completely missing BREAK row from chart notes and achievement."""
    if not isinstance(achievement, (int, float)) or isinstance(judgement.get("break"), dict):
        return None
    try:
        break_count = max(0, int(notes.get("break", 0)))
    except (TypeError, ValueError):
        return None
    if break_count <= 0:
        return None

    value_names = ("critical_perfect", "perfect", "great", "good", "miss")
    reference_counts = {name: 0 for name in value_names}
    for row_name in ("tap", "hold", "slide", "touch"):
        try:
            expected = max(0, int(notes.get(row_name, 0)))
        except (TypeError, ValueError):
            return None
        if expected <= 0:
            continue
        row = judgement.get(row_name)
        if not isinstance(row, dict):
            return None
        try:
            observed = sum(max(0, int(row.get(name, 0))) for name in value_names)
        except (TypeError, ValueError):
            return None
        if observed != expected:
            return None
        for name in value_names:
            reference_counts[name] += max(0, int(row.get(name, 0)))

    reference_total = sum(reference_counts.values())
    smoothing = 1.0
    reference_probabilities = {
        name: (reference_counts[name] + smoothing)
        / (reference_total + smoothing * len(value_names))
        for name in value_names
    }

    def distribution_penalty(row):
        counts = [max(0, int(row.get(name, 0))) for name in value_names]
        total = sum(counts)
        log_probability = math.lgamma(total + 1)
        log_probability -= sum(math.lgamma(count + 1) for count in counts)
        log_probability += sum(
            count * math.log(reference_probabilities[name])
            for name, count in zip(value_names, counts)
        )
        return -log_probability

    all_cp_row = {
        "critical_perfect": break_count,
        "perfect": 0,
        "great": 0,
        "good": 0,
        "miss": 0,
    }
    baseline_judgement = dict(judgement)
    baseline_judgement["break"] = all_cp_row
    baseline_range = calc_judgement_achievement_range(notes, baseline_judgement)
    if not baseline_range:
        return None
    baseline = (
        float(baseline_range["minimum"]) + float(baseline_range["maximum"])
    ) / 2
    target_deduction = baseline - float(achievement)
    if target_deduction < -0.001:
        return None

    scores = get_note_score(notes)
    required_scores = (
        "break_high_perfect",
        "break_low_perfect",
        "break_high_great",
        "break_low_great",
        "break_good",
        "break_miss",
    )
    if any(not isinstance(scores.get(name), (int, float)) for name in required_scores):
        return None
    perfect_min = float(scores["break_high_perfect"])
    perfect_max = float(scores["break_low_perfect"])
    great_min = float(scores["break_high_great"])
    great_max = float(scores["break_low_great"])
    good_score = float(scores["break_good"])
    miss_score = float(scores["break_miss"])
    if perfect_min <= 0 or perfect_max <= 0:
        return None

    # This loose bound only prunes impossible counts. Every retained row is
    # checked with the same rounded Calc function used by final validation.
    prune_tolerance = 0.003
    candidates = []
    iteration_count = 0
    for miss in range(break_count + 1):
        miss_deduction = miss * miss_score
        if miss_deduction > target_deduction + prune_tolerance:
            break
        for good in range(break_count - miss + 1):
            fixed_deduction = miss_deduction + good * good_score
            if fixed_deduction > target_deduction + prune_tolerance:
                break
            remaining = break_count - miss - good
            for great in range(remaining + 1):
                iteration_count += 1
                if iteration_count > 300_000:
                    return None
                minimum_without_perfect = fixed_deduction + great * great_min
                if minimum_without_perfect > target_deduction + prune_tolerance:
                    break
                maximum_without_perfect = fixed_deduction + great * great_max
                max_perfect_count = remaining - great
                perfect_low = max(
                    0,
                    math.ceil(
                        (target_deduction - prune_tolerance - maximum_without_perfect)
                        / perfect_max
                    ),
                )
                perfect_high = min(
                    max_perfect_count,
                    math.floor(
                        (target_deduction + prune_tolerance - minimum_without_perfect)
                        / perfect_min
                    ),
                )
                for perfect in range(perfect_low, perfect_high + 1):
                    row = {
                        "critical_perfect": remaining - great - perfect,
                        "perfect": perfect,
                        "great": great,
                        "good": good,
                        "miss": miss,
                    }
                    candidate_judgement = dict(judgement)
                    candidate_judgement["break"] = row
                    score_range = calc_judgement_achievement_range(
                        notes,
                        candidate_judgement,
                    )
                    if _calc_achievement_distance(achievement, score_range) != 0:
                        continue
                    midpoint = (
                        float(score_range["minimum"]) + float(score_range["maximum"])
                    ) / 2
                    candidate = {
                        "row": row,
                        "score_range": score_range,
                        "rank": (
                            distribution_penalty(row),
                            abs(float(achievement) - midpoint),
                            float(score_range["maximum"]) - float(score_range["minimum"]),
                            miss,
                            good,
                        ),
                    }
                    candidates.append(candidate)

    if not candidates:
        return None
    exact_candidates = []
    for candidate in sorted(candidates, key=lambda item: item["rank"]):
        candidate_judgement = dict(judgement)
        candidate_judgement["break"] = candidate["row"]
        detail = _infer_break_judgement_detail(
            notes,
            candidate_judgement,
            achievement,
        )
        if detail:
            candidate["break_detail"] = detail
            exact_candidates.append(candidate)
    if not exact_candidates:
        return None
    best_candidate = exact_candidates[0]
    return {
        "row": best_candidate["row"],
        "score_range": best_candidate["score_range"],
        "candidate_count": len(exact_candidates),
        "break_detail": best_candidate["break_detail"],
    }


def _infer_break_judgement_detail(notes, judgement, achievement):
    """Resolve the hidden two PERFECT and three GREAT grades for BREAK."""
    if not isinstance(achievement, (int, float)):
        return None
    break_row = judgement.get("break")
    if not isinstance(break_row, dict):
        return None
    try:
        break_count = max(0, int(notes.get("break", 0)))
        critical_perfect = max(0, int(break_row.get("critical_perfect", 0)))
        perfect = max(0, int(break_row.get("perfect", 0)))
        great = max(0, int(break_row.get("great", 0)))
        good = max(0, int(break_row.get("good", 0)))
        miss = max(0, int(break_row.get("miss", 0)))
    except (TypeError, ValueError):
        return None
    if critical_perfect + perfect + great + good + miss != break_count:
        return None

    score_judgements = {}
    for row_name in ("tap", "hold", "slide", "touch"):
        row = judgement.get(row_name) or {}
        for field_name in ("great", "good", "miss"):
            try:
                score_judgements[f"{row_name}_{field_name}"] = max(
                    0,
                    int(row.get(field_name, 0)),
                )
            except (TypeError, ValueError):
                return None
    score_judgements.update({
        "break_good": good,
        "break_miss": miss,
    })

    best_candidate = None
    candidate_count = 0
    iteration_count = 0
    for low_perfect in range(perfect + 1):
        high_perfect = perfect - low_perfect
        for low_great in range(great + 1):
            for middle_great in range(great - low_great + 1):
                iteration_count += 1
                if iteration_count > 100_000:
                    return None
                high_great = great - low_great - middle_great
                candidate_judgements = {
                    **score_judgements,
                    "break_high_perfect": high_perfect,
                    "break_low_perfect": low_perfect,
                    "break_high_great": high_great,
                    "break_middle_great": middle_great,
                    "break_low_great": low_great,
                }
                calculated = calc_score(notes, candidate_judgements)
                distance = abs(float(achievement) - calculated)
                if distance > 0.0006:
                    continue
                candidate = {
                    "critical_perfect": critical_perfect,
                    "perfect_high": high_perfect,
                    "perfect_low": low_perfect,
                    "great_high": high_great,
                    "great_middle": middle_great,
                    "great_low": low_great,
                    "good": good,
                    "miss": miss,
                    "calculated_achievement": calculated,
                    "rank": (
                        distance,
                        low_perfect,
                        low_great,
                        middle_great,
                    ),
                }
                candidate_count += 1
                if best_candidate is None or candidate["rank"] < best_candidate["rank"]:
                    best_candidate = candidate

    if best_candidate is None:
        return None
    best_candidate.pop("rank", None)
    best_candidate["candidate_count"] = candidate_count
    best_candidate["inferred"] = True
    return best_candidate


def _attach_break_loss_percentages(notes, break_detail):
    """Attach Calc note-score loss percentages used by result messages."""
    if not isinstance(break_detail, dict):
        return break_detail
    scores = get_note_score(notes)
    if not isinstance(scores, dict):
        return break_detail
    loss_percentages = {"critical_perfect": 0.0}
    score_keys = {
        "perfect_high": "break_high_perfect",
        "perfect_low": "break_low_perfect",
        "great_high": "break_high_great",
        "great_middle": "break_middle_great",
        "great_low": "break_low_great",
        "good": "break_good",
        "miss": "break_miss",
    }
    for detail_key, score_key in score_keys.items():
        value = scores.get(score_key)
        if isinstance(value, (int, float)):
            loss_percentages[detail_key] = float(value)
    break_detail["loss_percentages"] = loss_percentages
    return break_detail


def validate_recognized_judgement(
    result,
    ver="jp",
    allow_ocr_alignment=True,
    preserve_input=False,
):
    parsed = result.get("parsed") or {}
    title = str(parsed.get("title") or "").strip()
    judgement = parsed.get("sub_judgement") or {}
    if not judgement:
        return result

    songs, _ = read_dxdata(ver)
    if title:
        matching_songs, title_match_type = _match_recognized_song_title(
            title,
            songs,
            max_results=120,
        )
    else:
        matching_songs = [
            song for song in songs
            if not str(song.get("title") or "").strip()
        ]
        title_match_type = "blank"
    if not matching_songs:
        return result
    title_candidate_ranks = {
        _song_identity_key(song): index
        for index, song in enumerate(matching_songs)
    }

    row_names = ("tap", "hold", "slide", "touch", "break")
    value_names = ("critical_perfect", "perfect", "great", "good")
    all_value_names = (*value_names, "miss")

    def repair_overfull_normal_row(row_name, source_row, source_rows, note_counts):
        """Recover a JPEG-damaged normal row using chart totals and Calc."""
        if row_name == "break":
            return None
        try:
            expected = max(0, int(note_counts.get(row_name, 0) or 0))
            original = {
                name: max(0, int(source_row.get(name, 0) or 0))
                for name in all_value_names
            }
        except (TypeError, ValueError):
            return None
        if expected <= 0 or sum(original[name] for name in value_names) <= expected:
            return None

        # JPEG artifacts sometimes prepend grid fragments to a value (16 ->
        # 1016). Keep plausible numeric suffixes as repair starting points.
        bases = [original]
        for field_name in value_names:
            current = original[field_name]
            digits = str(current)
            if current <= expected or len(digits) < 4:
                continue
            for length in range(1, min(3, len(digits) - 1) + 1):
                suffix = int(digits[-length:])
                if suffix <= expected and suffix != current:
                    candidate = dict(original)
                    candidate[field_name] = suffix
                    bases.append(candidate)

        row_candidates = {}
        for base in bases:
            known = sum(base[name] for name in value_names)
            if known <= expected:
                candidate = dict(base)
                candidate["miss"] = expected - known
                row_candidates[tuple(candidate[name] for name in all_value_names)] = candidate
            if known < expected:
                continue
            for field_name in value_names:
                other_total = sum(
                    base[name] for name in value_names if name != field_name
                )
                replacement = expected - other_total
                if 0 <= replacement < base[field_name]:
                    candidate = dict(base)
                    candidate[field_name] = replacement
                    candidate["miss"] = 0
                    row_candidates[tuple(candidate[name] for name in all_value_names)] = candidate

        if not row_candidates:
            return None

        reference_counts = {name: 0 for name in all_value_names}
        for other_name, other_row in source_rows.items():
            if other_name == row_name or not isinstance(other_row, dict):
                continue
            try:
                other_expected = max(0, int(note_counts.get(other_name, 0) or 0))
                normalized = {
                    name: max(0, int(other_row.get(name, 0) or 0))
                    for name in all_value_names
                }
            except (TypeError, ValueError):
                continue
            other_known = sum(normalized[name] for name in value_names)
            if other_expected <= 0 or other_known > other_expected:
                continue
            normalized["miss"] = other_expected - other_known
            for name in all_value_names:
                reference_counts[name] += normalized[name]

        reference_total = sum(reference_counts.values())
        probabilities = {
            name: (reference_counts[name] + 1.0)
            / (reference_total + len(all_value_names))
            for name in all_value_names
        }

        def distribution_penalty(candidate):
            counts = [candidate[name] for name in all_value_names]
            total = sum(counts)
            log_probability = math.lgamma(total + 1)
            log_probability -= sum(math.lgamma(count + 1) for count in counts)
            log_probability += sum(
                count * math.log(probabilities[name])
                for name, count in zip(all_value_names, counts)
            )
            return -log_probability

        def calc_distance(candidate):
            tentative = {}
            for other_name, other_row in source_rows.items():
                if not isinstance(other_row, dict):
                    continue
                try:
                    other_expected = max(0, int(note_counts.get(other_name, 0) or 0))
                    normalized = {
                        name: max(0, int(other_row.get(name, 0) or 0))
                        for name in all_value_names
                    }
                except (TypeError, ValueError):
                    return float("inf")
                if other_name == row_name:
                    normalized = dict(candidate)
                else:
                    missing_fields = [
                        name for name in all_value_names if name not in other_row
                    ]
                    if len(missing_fields) == 1:
                        observed = sum(
                            normalized[name]
                            for name in all_value_names
                            if name != missing_fields[0]
                        )
                        inferred = other_expected - observed
                        if inferred >= 0:
                            normalized[missing_fields[0]] = inferred
                    other_known = sum(normalized[name] for name in value_names)
                    if other_known > other_expected:
                        return float("inf")
                    normalized["miss"] = other_expected - other_known
                tentative[other_name] = normalized
            score_range = calc_judgement_achievement_range(
                {
                    name: max(0, int(note_counts.get(name, 0) or 0))
                    for name in row_names
                },
                tentative,
            )
            distance = _calc_achievement_distance(achievement, score_range)
            return float("inf") if distance is None else distance

        ranked = sorted(
            row_candidates.values(),
            key=lambda candidate: (
                calc_distance(candidate),
                sum(candidate[name] != original[name] for name in all_value_names),
                sum(
                    {
                        "critical_perfect": 4,
                        "perfect": 3,
                        "great": 2,
                        "good": 1,
                        "miss": 1,
                    }[name]
                    for name in all_value_names
                    if candidate[name] != original[name]
                ),
                sum(abs(candidate[name] - original[name]) for name in all_value_names),
                distribution_penalty(candidate),
            ),
        )
        repaired = ranked[0]
        corrections = [
            {
                "row": row_name,
                "field": name,
                "ocr": original[name],
                "validated": repaired[name],
                "overfull_repair": True,
            }
            for name in value_names
            if repaired[name] != original[name]
        ]
        return repaired, corrections

    source_row_count = sum(
        1 for row in judgement.values()
        if isinstance(row, dict) and (
            preserve_input
            or any(int(value or 0) != 0 for value in row.values())
        )
    )
    achievement = parsed.get("achievement")
    candidates = []
    for song in matching_songs:
        for sheet in song.get("sheets", []):
            regions = sheet.get("regions") or {}
            if regions and regions.get(ver) is False:
                continue
            note_counts = sheet.get("noteCounts") or {}
            raw_overfull_rows = 0
            raw_matching_rows = 0
            for row_name in row_names:
                row = judgement.get(row_name)
                if not isinstance(row, dict):
                    continue
                try:
                    expected = max(0, int(note_counts.get(row_name, 0) or 0))
                    observed = sum(
                        max(0, int(row.get(name, 0) or 0))
                        for name in all_value_names
                    )
                except (TypeError, ValueError):
                    continue
                if observed > expected:
                    raw_overfull_rows += 1
                elif observed == expected:
                    raw_matching_rows += 1
            row_offsets = range(-2, 3) if allow_ocr_alignment else (0,)
            column_offsets = (-1, 0, 1) if allow_ocr_alignment else (0,)
            for row_offset in row_offsets:
                row_aligned = {}
                for source_index, source_name in enumerate(row_names):
                    row = judgement.get(source_name)
                    if not isinstance(row, dict) or (
                        not preserve_input
                        and not any(int(value or 0) != 0 for value in row.values())
                    ):
                        continue
                    target_index = source_index + row_offset
                    if 0 <= target_index < len(row_names):
                        row_aligned[row_names[target_index]] = dict(row)

                for column_offset in column_offsets:
                    aligned = {}
                    dropped_cells = 0
                    ignored_impossible_rows = []
                    inferred_single_cells = []
                    valid = True
                    for row_name, row in row_aligned.items():
                        shifted_row = {name: 0 for name in all_value_names}
                        try:
                            for source_index, source_name in enumerate(all_value_names):
                                value = max(0, int(row.get(source_name, 0)))
                                target_index = source_index + column_offset
                                if 0 <= target_index < len(all_value_names):
                                    shifted_row[all_value_names[target_index]] = value
                                elif value:
                                    dropped_cells += value
                        except (TypeError, ValueError):
                            valid = False
                            break
                        missing_fields = [
                            name for name in all_value_names
                            if name not in row
                        ]
                        if (
                            title_match_type == "exact"
                            and row_offset == 0
                            and column_offset == 0
                            and len(missing_fields) == 1
                        ):
                            expected = max(0, int(note_counts.get(row_name, 0) or 0))
                            observed = sum(
                                max(0, int(row.get(name, 0) or 0))
                                for name in all_value_names
                                if name in row
                            )
                            inferred = expected - observed
                            if inferred >= 0:
                                field_name = missing_fields[0]
                                shifted_row[field_name] = inferred
                                inferred_single_cells.append({
                                    "row": row_name,
                                    "field": field_name,
                                    "validated": inferred,
                                })
                        aligned[row_name] = shifted_row
                    if not valid:
                        continue

                    predicted_miss = {}
                    compared_rows = 0
                    matching_rows = 0
                    total_delta = 0
                    for row_name, row in list(aligned.items()):
                        expected = note_counts.get(row_name)
                        if expected is None:
                            expected = 0
                        try:
                            expected = int(expected)
                            known = sum(max(0, int(row.get(name, 0))) for name in value_names)
                            observed_miss = max(0, int(row.get("miss", 0)))
                        except (TypeError, ValueError):
                            valid = False
                            break
                        if (
                            expected <= 0
                            and (known > 0 or observed_miss > 0)
                            and not preserve_input
                            and title_match_type == "exact"
                            and row_offset == 0
                            and column_offset == 0
                        ):
                            for field_name in all_value_names:
                                previous = max(0, int(row.get(field_name, 0) or 0))
                                row[field_name] = 0
                                if previous:
                                    inferred_single_cells.append({
                                        "row": row_name,
                                        "field": field_name,
                                        "ocr": previous,
                                        "validated": 0,
                                        "zero_note_row_repair": True,
                                    })
                            known = 0
                            observed_miss = 0
                        if known > expected:
                            repaired_field = None
                            if (
                                not preserve_input
                                and title_match_type == "exact"
                                and row_offset == 0
                                and column_offset == 0
                            ):
                                repair = repair_overfull_normal_row(
                                    row_name,
                                    row,
                                    row_aligned,
                                    note_counts,
                                )
                                if repair:
                                    repaired_row, row_corrections = repair
                                    row.update(repaired_row)
                                    known = sum(
                                        max(0, int(row.get(name, 0)))
                                        for name in value_names
                                    )
                                    repaired_field = row_name
                                    inferred_single_cells.extend(row_corrections)
                            if repaired_field is not None and known <= expected:
                                calculated_miss = expected - known
                                predicted_miss[row_name] = calculated_miss
                                compared_rows += 1
                                total_delta += abs(calculated_miss - observed_miss)
                                if calculated_miss == observed_miss:
                                    matching_rows += 1
                                continue
                            if (
                                allow_ocr_alignment
                                and not preserve_input
                                and title_match_type == "exact"
                                and row_offset == 0
                                and column_offset == 0
                                and row_name == "break"
                                and len(aligned) >= 5
                            ):
                                ignored_impossible_rows.append(row_name)
                                del aligned[row_name]
                                continue
                            valid = False
                            break
                        calculated_miss = expected - known
                        predicted_miss[row_name] = calculated_miss
                        compared_rows += 1
                        total_delta += abs(calculated_miss - observed_miss)
                        if calculated_miss == observed_miss:
                            matching_rows += 1
                    if valid and compared_rows >= 3:
                        calculated_rows = {
                            row_name: dict(row)
                            for row_name, row in aligned.items()
                        }
                        if not preserve_input:
                            for row_name, calculated_miss in predicted_miss.items():
                                calculated_rows[row_name]["miss"] = calculated_miss
                        notes = {
                            row_name: int(note_counts.get(row_name, 0) or 0)
                            for row_name in row_names
                        }
                        achievement_range = calc_judgement_achievement_range(
                            notes,
                            calculated_rows,
                        )
                        achievement_distance = _calc_achievement_distance(
                            achievement,
                            achievement_range,
                        )
                        candidates.append({
                            "song": song,
                            "sheet": sheet,
                            "aligned": aligned,
                            "row_offset": row_offset,
                            "column_offset": column_offset,
                            "dropped_rows": source_row_count - len(aligned),
                            "unexpected_dropped_rows": max(
                                0,
                                source_row_count
                                - len(aligned)
                                - len(ignored_impossible_rows),
                            ),
                            "dropped_cells": dropped_cells,
                            "ignored_impossible_rows": ignored_impossible_rows,
                            "inferred_single_cells": inferred_single_cells,
                            "overfull_repair_count": sum(
                                bool(item.get("overfull_repair"))
                                for item in inferred_single_cells
                            ),
                            "overfull_repair_delta": sum(
                                abs(
                                    int(item.get("validated", 0) or 0)
                                    - int(item.get("ocr", 0) or 0)
                                )
                                for item in inferred_single_cells
                                if item.get("overfull_repair")
                            ),
                            "miss": predicted_miss,
                            "compared_rows": compared_rows,
                            "matching_rows": matching_rows,
                            "delta": total_delta,
                            "notes": notes,
                            "achievement_range": achievement_range,
                            "achievement_distance": achievement_distance,
                            "raw_overfull_rows": raw_overfull_rows,
                            "raw_matching_rows": raw_matching_rows,
                            "title_candidate_rank": title_candidate_ranks.get(
                                _song_identity_key(song),
                                len(title_candidate_ranks),
                            ),
                        })

    if not candidates:
        return result
    trusted_title_match_types = {
        "exact",
        "blank",
        "ocr_confusable",
        "ocr_kana",
        "rolling_exact",
        "rolling_partial",
        "rolling_fuzzy",
        "edge_fuzzy",
        "edit_fuzzy",
        "ocr_embedded",
        "prefix",
    }
    prefer_achievement_alignment = (
        title_match_type in trusted_title_match_types
        and achievement is not None
    )

    def candidate_sort_key(item):
        achievement_distance = item["achievement_distance"]
        alignment_score = (
            achievement_distance
            if prefer_achievement_alignment and achievement_distance is not None
            else (float("inf") if prefer_achievement_alignment else 0)
        )
        return (
            item["unexpected_dropped_rows"],
            item["raw_overfull_rows"],
            -item["raw_matching_rows"],
            alignment_score,
            -item["matching_rows"],
            item["compared_rows"] - item["matching_rows"],
            item["delta"],
            item["title_candidate_rank"],
            0 if (
                title_match_type == "exact"
                and item["row_offset"] == 0
                and item["column_offset"] == 0
                and item["ignored_impossible_rows"] == ["break"]
            ) else 1,
            achievement_distance if achievement_distance is not None else 0,
            item["overfull_repair_count"],
            item["overfull_repair_delta"],
            item["dropped_cells"],
            abs(item["row_offset"]),
            abs(item["column_offset"]),
        )

    candidates.sort(key=candidate_sort_key)
    best = candidates[0]
    unshifted_chart_keys = {
        (
            str(item["song"].get("id") or ""),
            str(item["song"].get("type") or ""),
            str(item["sheet"].get("difficulty") or ""),
        )
        for item in candidates
        if item["row_offset"] == 0 and item["column_offset"] == 0
    }
    minimum_matching_rows = max(2, best["compared_rows"] - 2)
    exact_unique_unshifted_match = (
        title_match_type in trusted_title_match_types
        and best["row_offset"] == 0
        and best["column_offset"] == 0
        and best["compared_rows"] >= 4
        and len(unshifted_chart_keys) == 1
    )
    exact_unshifted_match = (
        title_match_type in trusted_title_match_types
        and best["row_offset"] == 0
        and best["column_offset"] == 0
        and best["compared_rows"] >= 4
        and best["matching_rows"] >= 2
    )
    if (
        best["matching_rows"] < minimum_matching_rows
        and not exact_unshifted_match
        and not exact_unique_unshifted_match
    ):
        return result
    if best["row_offset"] != 0 and best["matching_rows"] < 3:
        return result
    if len(candidates) > 1 and not exact_unique_unshifted_match:
        second = candidates[1]
        if (
            second["matching_rows"] == best["matching_rows"]
            and second["delta"] == best["delta"]
            and second["achievement_distance"] == best["achievement_distance"]
            and (
                second["miss"] != best["miss"]
                or second["row_offset"] != best["row_offset"]
                or second["column_offset"] != best["column_offset"]
            )
        ):
            return result

    judgement = best["aligned"]
    for row_name, expected_notes in best["notes"].items():
        if int(expected_notes or 0) == 0 and not isinstance(judgement.get(row_name), dict):
            judgement[row_name] = {
                field_name: 0
                for field_name in all_value_names
            }
    parsed["sub_judgement"] = judgement
    corrections = {}
    if not preserve_input:
        for row_name, calculated_miss in best["miss"].items():
            row = judgement.get(row_name)
            if not isinstance(row, dict):
                continue
            previous = row.get("miss", 0)
            row["miss"] = calculated_miss
            if previous != calculated_miss:
                corrections[row_name] = {"ocr": previous, "validated": calculated_miss}

    song = best["song"]
    sheet = best["sheet"]
    achievement_distance = best["achievement_distance"]
    achievement_range = best["achievement_range"]
    calc_uncertainties = []
    calc_corrections = [
        {**item, "ocr": item.get("ocr"), "single_missing_cell": True}
        for item in best.get("inferred_single_cells", [])
    ]
    break_inference = None
    if not preserve_input:
        break_inference = _infer_missing_break_judgement(
            best["notes"],
            judgement,
            achievement,
        )
    if break_inference:
        judgement["break"] = break_inference["row"]
        parsed["sub_judgement"] = judgement
        achievement_range = break_inference["score_range"]
        achievement_distance = _calc_achievement_distance(
            achievement,
            achievement_range,
        )
        calc_corrections.append({
            "row": "break",
            "field": "row",
            "inferred_row": True,
            "validated_row": break_inference["row"],
            "candidate_count": break_inference["candidate_count"],
        })
    if achievement_distance is not None and achievement_distance > 0:
        calc_uncertainties = _find_calc_judgement_uncertainties(
            best["notes"],
            judgement,
            achievement,
        )
        resolution = None
        if not preserve_input:
            resolution = _apply_same_row_miss_redistribution(
                best["notes"],
                judgement,
                achievement,
                calc_uncertainties,
            )
            if not resolution:
                resolution = _apply_calc_row_balance(
                    best["notes"],
                    judgement,
                    achievement,
                    calc_uncertainties,
                )
            if not resolution:
                resolution = _apply_unique_calc_judgement_correction(
                    best["notes"],
                    judgement,
                    achievement,
                    calc_uncertainties,
                )
        if resolution:
            judgement = resolution["judgement"]
            parsed["sub_judgement"] = judgement
            achievement_range = resolution["score_range"]
            achievement_distance = 0.0
            resolution_corrections = (
                resolution.get("corrections")
                or [resolution["correction"]]
            )
            calc_corrections.extend(resolution_corrections)
            calc_uncertainties = []

            row_name = resolution_corrections[0]["row"]
            if row_name in corrections:
                original_miss = corrections[row_name]["ocr"]
                final_miss = resolution_corrections[0]["miss_validated"]
                if original_miss == final_miss:
                    del corrections[row_name]
                else:
                    corrections[row_name]["validated"] = final_miss
    else:
        for row_name, expected in best["notes"].items():
            if expected > 0 and not isinstance(judgement.get(row_name), dict):
                calc_uncertainties.append({
                    "row": row_name,
                    "field": "row",
                    "ocr": None,
                    "candidate_min": None,
                    "candidate_max": None,
                    "candidate_count": 0,
                    "miss_min": None,
                    "miss_max": None,
                    "row_missing": True,
                })
    break_detail = (
        break_inference.get("break_detail")
        if break_inference
        else _infer_break_judgement_detail(
            best["notes"],
            judgement,
            achievement,
        )
    )
    if break_detail and break_inference:
        break_detail["row_candidate_count"] = break_inference["candidate_count"]
    break_detail = _attach_break_loss_percentages(best["notes"], break_detail)
    loss_percentages = get_note_score(best["notes"])
    canonical_title = song.get("title")
    parsed["title"] = canonical_title if canonical_title is not None else title
    result["validation"] = {
        "song_id": song.get("id"),
        "title": song.get("title"),
        "type": song.get("type"),
        "cover_url": song.get("cover_url"),
        "cover_name": song.get("cover_name"),
        "difficulty": sheet.get("difficulty"),
        "level": sheet.get("level"),
        "internal_level": sheet.get("internalLevelValue"),
        "title_match_type": title_match_type,
        "exact_title_match": title_match_type in {"exact", "blank"},
        "compared_rows": best["compared_rows"],
        "matching_rows": best["matching_rows"],
        "row_offset": best["row_offset"],
        "column_offset": best["column_offset"],
        "miss_corrections": corrections,
        "achievement_calc": {
            "observed": achievement,
            "minimum": (
                achievement_range.get("minimum")
                if achievement_range else None
            ),
            "maximum": (
                achievement_range.get("maximum")
                if achievement_range else None
            ),
            "consistent": achievement_distance == 0 if achievement_distance is not None else None,
            "complete": not any(item.get("row_missing") for item in calc_uncertainties),
        },
        "calc_corrections": calc_corrections,
        "uncertain_cells": calc_uncertainties,
        "break_detail": break_detail,
        "loss_percentages": loss_percentages,
    }
    return result


def _parse_fix_record_command(command_text):
    lines = [line.strip() for line in str(command_text or "").splitlines() if line.strip()]
    if not lines or lines[0].lower() == "fix-rcd-help":
        return None
    title_match = re.fullmatch(r"fix-rcd\s+(.+)", lines[0], re.IGNORECASE)
    if not title_match:
        return None
    if len(lines) != 7:
        raise ValueError("fix-rcd requires a title, achievement, and five judgement rows")

    title = re.sub(r"\s+\[(?:DX|STD)\]\s*$", "", title_match.group(1), flags=re.IGNORECASE).strip()
    if title in {'""', "''"}:
        title = ""

    achievement_match = re.fullmatch(r"(\d{1,3}(?:[.,]\d{1,4})?)%?", lines[1])
    if not achievement_match:
        raise ValueError("achievement must be a percentage between 0 and 101")
    achievement = float(achievement_match.group(1).replace(",", "."))
    if not 0 <= achievement <= 101:
        raise ValueError("achievement must be a percentage between 0 and 101")

    row_names = ("tap", "hold", "slide", "touch", "break")
    field_names = ("critical_perfect", "perfect", "great", "good", "miss")
    judgement = {}
    for row_name, line in zip(row_names, lines[2:]):
        row_match = re.fullmatch(r"(\d{1,4})/(\d{1,4})/(\d{1,4})/(\d{1,4})/(\d{1,4})", line)
        if not row_match:
            raise ValueError("each judgement row must contain five slash-separated integers")
        judgement[row_name] = {
            field_name: int(value)
            for field_name, value in zip(field_names, row_match.groups())
        }
    return title, achievement, judgement


def parse_fix_record_command(command_text):
    return _parse_fix_record_command(command_text)


def score_recognition_needs_manual_fix(result) -> bool:
    validation = result.get("validation") or {}
    judgement = (result.get("parsed") or {}).get("sub_judgement") or {}
    achievement_calc = validation.get("achievement_calc") or {}
    uncertain_cells = validation.get("uncertain_cells") or []
    fully_validated = (
        bool(validation.get("song_id"))
        and achievement_calc.get("consistent") is True
        and achievement_calc.get("complete") is True
        and not uncertain_cells
    )
    has_judgement_data = any(
        isinstance(judgement.get(row_name), dict)
        for row_name in ("tap", "hold", "slide", "touch", "break")
    )
    return has_judgement_data and not fully_validated


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


def build_score_crop_preview_image(image_bytes: bytes) -> Image.Image:
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

    from score_result_cropper import crop_result_fields_in_memory

    metadata = crop_result_fields_in_memory(image)
    field_order = (
        "main_title",
        "main_achievement",
        "sub_judgement_table",
    )
    crops = [
        (field_name, metadata["fields"][field_name]["image"].convert("RGB"))
        for field_name in field_order
        if field_name in metadata.get("fields", {})
    ]
    if not crops:
        raise InvalidScoreImageError("No score result crop fields were detected")

    card_width = 640
    card_header_height = 36
    card_body_height = 260
    card_padding = 14
    gap = 20
    columns = 2 if len(crops) > 1 else 1
    rows = math.ceil(len(crops) / columns)
    canvas_width = columns * card_width + (columns + 1) * gap
    canvas_height = rows * (card_header_height + card_body_height) + (rows + 1) * gap
    canvas = Image.new("RGB", (canvas_width, canvas_height), "#f2f4f8")
    draw = ImageDraw.Draw(canvas)

    for index, (field_name, crop) in enumerate(crops):
        row, column = divmod(index, columns)
        x = gap + column * (card_width + gap)
        y = gap + row * (card_header_height + card_body_height + gap)
        draw.rounded_rectangle(
            (x, y, x + card_width, y + card_header_height),
            radius=10,
            fill="#111827",
        )
        draw.text((x + 14, y + 10), field_name, fill="#ffffff")

        body_x = x
        body_y = y + card_header_height
        draw.rectangle(
            (body_x, body_y, body_x + card_width, body_y + card_body_height),
            fill="#ffffff",
        )
        max_width = card_width - card_padding * 2
        max_height = card_body_height - card_padding * 2
        scale = min(max_width / crop.width, max_height / crop.height)
        resized = crop.resize(
            (
                max(1, int(round(crop.width * scale))),
                max(1, int(round(crop.height * scale))),
            ),
            Image.Resampling.LANCZOS,
        )
        paste_x = body_x + (card_width - resized.width) // 2
        paste_y = body_y + (card_body_height - resized.height) // 2
        canvas.paste(resized, (paste_x, paste_y))

    return canvas


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
