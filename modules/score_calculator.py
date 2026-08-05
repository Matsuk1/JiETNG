from decimal import Decimal, ROUND_DOWN


NOTE_BASES = {
    "tap": (500, 400, 250),
    "hold": (1000, 800, 500),
    "slide": (1500, 1200, 750),
    "touch": (500, 400, 250),
}
BREAK_SCORES = {
    "critical": (2500, 100),
    "high_perfect": (2500, 75),
    "low_perfect": (2500, 50),
    "high_great": (2000, 40),
    "middle_great": (1500, 40),
    "low_great": (1250, 40),
    "good": (1000, 30),
}
NOTE_JUDGEMENTS = ("full", "great", "good", "miss")
RECORDED_NOTE_JUDGEMENTS = NOTE_JUDGEMENTS[1:]
BREAK_JUDGEMENTS = tuple(BREAK_SCORES)
RECORDED_BREAK_JUDGEMENTS = (*BREAK_JUDGEMENTS[1:], "miss")


def _truncate_decimal(value, places):
    quantum = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantum, rounding=ROUND_DOWN)


def _calculate_judgement_scores(notes, places=7):
    counts = {name: notes[name] or 0 for name in (*NOTE_BASES, "break")}
    total_base = sum(counts[name] * values[0] for name, values in NOTE_BASES.items())
    total_base += counts["break"] * 2500
    break_add_total = counts["break"] * 100
    if not total_base or not break_add_total:
        return {}

    def value(base, add=0):
        score = Decimal(base * 100) / Decimal(total_base)
        if add:
            score += Decimal(add) / Decimal(break_add_total)
        return _truncate_decimal(score, places) if places is not None else score

    scores = {}
    for note_type, (full, great, good) in NOTE_BASES.items():
        scores.update(
            {
                f"{note_type}_full": value(full),
                f"{note_type}_great": value(great),
                f"{note_type}_good": value(good),
                f"{note_type}_miss": Decimal("0"),
            }
        )
    scores.update(
        {
            f"break_{name}": value(base, add)
            for name, (base, add) in BREAK_SCORES.items()
        }
    )
    scores["break_miss"] = Decimal("0")
    return scores


def get_note_score(notes):
    """Return the displayed achievement loss for each non-critical judgement."""
    scores = _calculate_judgement_scores(notes)
    if not scores:
        return {}

    losses = {}
    for note_type in NOTE_BASES:
        for judgement in RECORDED_NOTE_JUDGEMENTS:
            losses[f"{note_type}_{judgement}"] = float(
                _truncate_decimal(
                    scores[f"{note_type}_full"] - scores[f"{note_type}_{judgement}"], 7
                )
            )
    for judgement in RECORDED_BREAK_JUDGEMENTS:
        losses[f"break_{judgement}"] = float(
            _truncate_decimal(
                scores["break_critical"] - scores[f"break_{judgement}"], 7
            )
        )
    return losses


def calc_score_precise(notes, judgements):
    """Return the exact achievement before four-decimal display truncation."""
    scores = _calculate_judgement_scores(notes, places=None)
    if not scores:
        return Decimal("0")

    total = Decimal("0")
    for note_type in NOTE_BASES:
        counts = [
            int(judgements.get(f"{note_type}_{name}", 0) or 0)
            for name in RECORDED_NOTE_JUDGEMENTS
        ]
        counts.insert(0, max(0, int(notes.get(note_type, 0) or 0) - sum(counts)))
        for name, count in zip(NOTE_JUDGEMENTS[:3], counts[:3]):
            total += scores[f"{note_type}_{name}"] * count

    break_counts = [
        int(judgements.get(f"break_{name}", 0) or 0)
        for name in RECORDED_BREAK_JUDGEMENTS
    ]
    break_counts.insert(0, max(0, int(notes.get("break", 0) or 0) - sum(break_counts)))
    for name, count in zip(BREAK_JUDGEMENTS, break_counts):
        total += scores[f"break_{name}"] * count
    return total


def calc_score(notes, judgements):
    """Return the achievement truncated to the game's four-decimal display."""
    return float(
        calc_score_precise(notes, judgements).quantize(Decimal("0.0001"), ROUND_DOWN)
    )


def calc_judgement_achievement_range(notes, judgement_rows):
    """Return the display range when BREAK sub-grades are unknown."""
    if not isinstance(judgement_rows, dict):
        return None

    high, low = {}, {}
    try:
        for note_type in NOTE_BASES:
            row = judgement_rows.get(note_type) or {}
            for name in ("great", "good", "miss"):
                high[f"{note_type}_{name}"] = low[f"{note_type}_{name}"] = max(
                    0, int(row.get(name, 0))
                )
        break_row = judgement_rows.get("break") or {}
        for name in ("perfect", "great", "good", "miss"):
            count = max(0, int(break_row.get(name, 0)))
            if name in ("perfect", "great"):
                high[f"break_high_{name}"] = count
                low[f"break_low_{name}"] = count
            else:
                high[f"break_{name}"] = low[f"break_{name}"] = count
    except (TypeError, ValueError):
        return None

    endpoints = calc_score(notes, low), calc_score(notes, high)
    return {"minimum": min(endpoints), "maximum": max(endpoints)}
