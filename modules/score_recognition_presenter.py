"""Presentation values derived from score-recognition results."""

import re

JUDGEMENT_ROWS = ("tap", "hold", "slide", "touch", "break")

COMBO_ICON_FILES = {
    "fc": "fc.png",
    "fcp": "fcplus.png",
    "ap": "ap.png",
    "app": "applus.png",
    "dummy": "fc_dummy.png",
}

DIFFICULTY_STYLES = {
    "basic": {"bg": "#75B520", "text": "#FFFFFF", "metric": "#75B520"},
    "advanced": {"bg": "#EFA508", "text": "#111111", "metric": "#B36F00"},
    "expert": {"bg": "#CC4D59", "text": "#FFFFFF", "metric": "#CC4D59"},
    "master": {"bg": "#9F51DC", "text": "#FFFFFF", "metric": "#8E44AD"},
    "remaster": {"bg": "#E9D4F3", "text": "#72148D", "metric": "#B06FD3"},
    "utage": {"bg": "#F52EDD", "text": "#FFFFFF", "metric": "#D10FBA"},
}
DEFAULT_DIFFICULTY_STYLE = {"bg": "#315B7D", "text": "#FFFFFF", "metric": "#315B7D"}

DIFFICULTY_LABELS = {
    "basic": "BASIC",
    "advanced": "ADVANCED",
    "expert": "EXPERT",
    "master": "MASTER",
    "remaster": "Re:MASTER",
    "utage": "U·TA·GE",
}

RANK_THRESHOLDS = (
    (100.5, "sssp"), (100.0, "sss"), (99.5, "ssp"), (99.0, "ss"),
    (98.0, "sp"), (97.0, "s"), (94.0, "aaa"), (90.0, "aa"),
    (80.0, "a"), (75.0, "bbb"), (70.0, "bb"), (60.0, "b"),
    (50.0, "c"), (0.0, "d"),
)


def combo_status(judgement, achievement):
    if any(not isinstance(judgement.get(row), dict) for row in JUDGEMENT_ROWS):
        return None
    totals = {field: 0 for field in ("great", "good", "miss")}
    try:
        for row_name in JUDGEMENT_ROWS:
            for field in totals:
                totals[field] += nonnegative_count(judgement[row_name].get(field))
    except (TypeError, ValueError):
        return None
    if isinstance(achievement, (int, float)) and achievement >= 100.99995:
        return "app"
    if not any(totals.values()):
        return "ap"
    if totals["good"] == 0 and totals["miss"] == 0:
        return "fcp"
    if totals["miss"] == 0:
        return "fc"
    return "dummy"


def score_rank(achievement):
    if not isinstance(achievement, (int, float)):
        return None
    return next((name for threshold, name in RANK_THRESHOLDS if achievement >= threshold), "d")


def difficulty_presentation(difficulty):
    key = str(difficulty or "").lower()
    return (
        DIFFICULTY_STYLES.get(key, DEFAULT_DIFFICULTY_STYLE),
        DIFFICULTY_LABELS.get(key, str(difficulty or "").strip() or "-"),
    )


def nonnegative_count(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def format_loss_percentage(value, count=1):
    if not isinstance(value, (int, float)):
        return "-"
    loss = float(value) * nonnegative_count(count)
    return "0.0000%" if abs(loss) < 0.00005 else f"-{loss:.4f}%"


def build_fix_command(judgement, song_title, achievement):
    rows = []
    for row_name in JUDGEMENT_ROWS:
        row = judgement.get(row_name)
        row = row if isinstance(row, dict) else {}
        rows.append("/".join(
            str(nonnegative_count(row.get(field)))
            for field in ("critical_perfect", "perfect", "great", "good", "miss")
        ))
    title = re.sub(r"\s+", " ", song_title).strip() or '""'
    achievement_text = f"{achievement:.4f}%" if isinstance(achievement, (int, float)) else "0.0000%"
    return "\n".join((f"fix-rcd {title}", achievement_text, *rows))


def calc_status(validation, uncertain_cells, translate):
    calculation = validation.get("achievement_calc") or {}
    corrections = validation.get("calc_corrections") or []
    inferred = any(isinstance(item, dict) and item.get("inferred_row") for item in corrections)
    consistent = calculation.get("consistent")
    if consistent is None:
        return None, inferred

    if corrections:
        labels = {"critical_perfect": "CP", "perfect": "PF", "great": "GR", "good": "GD"}
        lines = []
        for correction in corrections:
            if correction.get("inferred_row"):
                continue
            row = str(correction.get("row") or "").upper()
            field = labels.get(correction.get("field"), str(correction.get("field") or "").upper())
            if correction.get("calc_completion"):
                amount = correction.get("amount", correction.get("added", 0))
                lines.append(f"{row} {field} {'+' if amount >= 0 else ''}{amount}")
            else:
                lines.append(
                    f"{row} {field} {correction.get('ocr')}→{correction.get('validated')} / "
                    f"MS {correction.get('miss_ocr')}→{correction.get('miss_validated')}"
                )
        text = translate("calc_inferred" if inferred else "calc_corrected")
        if lines:
            text += "\n" + "\n".join(lines)
    elif consistent and uncertain_cells:
        text = translate("calc_incomplete")
    elif consistent:
        text = translate("calc_validated")
    else:
        text = translate("calc_uncertain" if uncertain_cells else "calc_mismatch")
        values = (calculation.get("minimum"), calculation.get("maximum"), calculation.get("observed"))
        if all(isinstance(value, (int, float)) for value in values):
            text += f"\nCalc {values[0]:.4f}%-{values[1]:.4f}% / OCR {values[2]:.4f}%"
    return (text, consistent), inferred
