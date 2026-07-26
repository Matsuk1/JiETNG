"""Stable public response contract for score-result recognition."""
from __future__ import annotations

from typing import Any


JUDGEMENT_ROWS = ("tap", "hold", "slide", "touch", "break")
JUDGEMENT_FIELDS = (
    "critical_perfect",
    "perfect",
    "great",
    "good",
    "miss",
)
BREAK_DETAIL_FIELDS = (
    "critical_perfect",
    "perfect_high",
    "perfect_low",
    "great_high",
    "great_middle",
    "great_low",
    "good",
    "miss",
    "candidate_count",
    "row_candidate_count",
)
CALC_CORRECTION_FIELDS = (
    "row",
    "field",
    "ocr",
    "validated",
    "miss_ocr",
    "miss_validated",
    "inferred_row",
    "candidate_count",
)
UNCERTAIN_CELL_FIELDS = (
    "row",
    "field",
    "ocr",
    "candidate_min",
    "candidate_max",
    "candidate_count",
    "miss_min",
    "miss_max",
    "row_missing",
)


class ScoreRecognitionResultError(ValueError):
    """The OCR result cannot be exposed as a complete score result."""


def _selected_mapping(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {field: value.get(field) for field in fields if field in value}


def _selected_list(value: Any, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        selected = _selected_mapping(item, fields)
        if isinstance(item, dict) and isinstance(item.get("validated_row"), dict):
            selected["validated_row"] = {
                field: max(0, int(item["validated_row"].get(field, 0) or 0))
                for field in JUDGEMENT_FIELDS
            }
        if selected:
            result.append(selected)
    return result


def _miss_corrections(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    return {
        row_name: _selected_mapping(correction, ("ocr", "validated"))
        for row_name, correction in value.items()
        if isinstance(correction, dict)
    }


def _complete_judgements(value: Any) -> dict[str, dict[str, int]]:
    if not isinstance(value, dict):
        raise ScoreRecognitionResultError("No complete judgement data was recognized")

    result: dict[str, dict[str, int]] = {}
    for row_name in JUDGEMENT_ROWS:
        row = value.get(row_name)
        if not isinstance(row, dict):
            raise ScoreRecognitionResultError(
                f"Judgement row '{row_name}' was not recognized"
            )
        try:
            result[row_name] = {
                field_name: max(0, int(row.get(field_name, 0) or 0))
                for field_name in JUDGEMENT_FIELDS
            }
        except (TypeError, ValueError) as exc:
            raise ScoreRecognitionResultError(
                f"Judgement row '{row_name}' contains an invalid value"
            ) from exc
    return result


def build_score_recognition_response(result: Any) -> dict[str, Any]:
    """Convert an internal OCR result into the documented API response."""
    if not isinstance(result, dict):
        raise ScoreRecognitionResultError("OCR did not return a result")

    parsed = result.get("parsed")
    validation = result.get("validation")
    if not isinstance(parsed, dict) or not isinstance(validation, dict):
        raise ScoreRecognitionResultError(
            "The score could not be matched to a song and chart"
        )

    song_id = validation.get("song_id")
    if song_id is None or song_id == "":
        raise ScoreRecognitionResultError("The recognized song could not be identified")

    achievement = parsed.get("achievement")
    if not isinstance(achievement, (int, float)):
        raise ScoreRecognitionResultError("Achievement was not recognized")

    judgements = _complete_judgements(parsed.get("sub_judgement"))
    break_detail = _selected_mapping(
        validation.get("break_detail"),
        BREAK_DETAIL_FIELDS,
    )
    return {
        "success": True,
        "song": {
            "id": song_id,
            "title": validation.get("title"),
            "type": validation.get("type"),
        },
        "chart": {
            "difficulty": validation.get("difficulty"),
            "level": validation.get("level"),
            "internal_level": validation.get("internal_level"),
        },
        "score": {
            "achievement": float(achievement),
            "judgements": judgements,
            "break_detail": break_detail,
        },
        "validation": {
            "title_match_type": validation.get("title_match_type"),
            "exact_title_match": bool(validation.get("exact_title_match")),
            "compared_rows": validation.get("compared_rows"),
            "matching_rows": validation.get("matching_rows"),
            "row_offset": validation.get("row_offset"),
            "column_offset": validation.get("column_offset"),
            "miss_corrections": _miss_corrections(
                validation.get("miss_corrections")
            ),
            "achievement_calc": _selected_mapping(
                validation.get("achievement_calc"),
                ("observed", "minimum", "maximum", "consistent", "complete"),
            ),
            "calc_corrections": _selected_list(
                validation.get("calc_corrections"),
                CALC_CORRECTION_FIELDS,
            ),
            "uncertain_cells": _selected_list(
                validation.get("uncertain_cells"),
                UNCERTAIN_CELL_FIELDS,
            ),
        },
    }
