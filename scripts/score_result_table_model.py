#!/usr/bin/env python3
"""Run the high-accuracy Paddle table pipeline in an isolated process."""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import tempfile
from io import BytesIO

os.environ.setdefault("MPLCONFIGDIR", "/tmp/jietng-matplotlib")

CPU_THREADS = max(1, int(os.getenv(
    "JIETNG_TABLE_OCR_CPU_THREADS",
    str(min(8, os.cpu_count() or 1)),
)))
ENABLE_MKLDNN = os.getenv(
    "JIETNG_TABLE_OCR_ENABLE_MKLDNN",
    "0",
) == "1"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "1" if ENABLE_MKLDNN else "0"
os.environ["FLAGS_use_onednn"] = "1" if ENABLE_MKLDNN else "0"
os.environ["FLAGS_use_mkldnn"] = "1" if ENABLE_MKLDNN else "0"
os.environ.setdefault("PADDLE_PDX_CPU_NUM_THREADS", str(CPU_THREADS))

PROTOCOL_STDOUT = sys.stdout
sys.stdout = sys.stderr

from bs4 import BeautifulSoup
from PIL import Image
from paddleocr import TableRecognitionPipelineV2


ROW_NAMES = ("tap", "hold", "slide", "touch", "break")
COLUMN_NAMES = ("critical_perfect", "perfect", "great", "good", "miss")
RESULT_MARKER = "JIETNG_TABLE_RESULT="
READY_MARKER = "JIETNG_TABLE_READY"
NUMERIC_OCR_TRANSLATION = str.maketrans({
    "O": "0",
    "o": "0",
    "〇": "0",
    "Z": "2",
    "z": "2",
})


def _row_name(text: str) -> str | None:
    normalized = re.sub(r"[^A-Z]", "", text.upper())
    return next((name for name in ROW_NAMES if name.upper() in normalized), None)


def _numeric_cell(text: str) -> int | None:
    normalized = re.sub(r"\s+", "", text).translate(NUMERIC_OCR_TRANSLATION)
    return int(normalized) if re.fullmatch(r"\d+", normalized) else None


def _parse_html_table_partial(html: str) -> dict[str, dict[str, int]]:
    soup = BeautifulSoup(html, "html.parser")
    parsed_rows: list[tuple[str | None, list[int]]] = []
    for table_row in soup.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in table_row.find_all("td")]
        values = [value for cell in cells if (value := _numeric_cell(cell)) is not None]
        if len(values) != len(COLUMN_NAMES):
            continue
        label = next((_row_name(cell) for cell in cells if _row_name(cell)), None)
        parsed_rows.append((label, values))

    result: dict[str, dict[str, int]] = {}
    for index, (label, values) in enumerate(parsed_rows):
        row_name = label or next(
            (name for name in ROW_NAMES[index:] if name not in result),
            None,
        )
        if row_name is None:
            return {}
        if row_name in result:
            return {}
        values = _normalize_row_values(row_name, values)
        result[row_name] = dict(zip(COLUMN_NAMES, values))
    return result


def _normalize_row_values(row_name: str, values: list[int]) -> list[int]:
    if (
        row_name == "break"
        and len(values) == len(COLUMN_NAMES)
        and values[0] == 0
        and values[1] > 0
        and values[2] > 0
        and values[3] == 0
        and values[4] == 0
    ):
        return values[1:] + [0]
    return values


def _parse_html_table(html: str) -> dict[str, dict[str, int]] | None:
    result = _parse_html_table_partial(html)
    return result if set(result) == set(ROW_NAMES) else None


def _create_pipeline() -> TableRecognitionPipelineV2:
    return TableRecognitionPipelineV2(
        device="cpu",
        enable_mkldnn=ENABLE_MKLDNN,
        mkldnn_cache_capacity=64,
        cpu_threads=CPU_THREADS,
        text_detection_model_name="PP-OCRv6_small_det",
        text_recognition_model_name="PP-OCRv6_small_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_layout_detection=False,
        use_ocr_model=True,
    )


def _parse_table_outputs(
    outputs,
) -> tuple[
    dict[str, dict[str, int]] | None,
    list[list[list[str]]],
    dict[str, dict[str, int]],
]:
    candidates = []
    partial_candidates: list[dict[str, dict[str, int]]] = []
    rejected_tables: list[list[list[str]]] = []
    for output in outputs:
        payload = output.json() if callable(getattr(output, "json", None)) else output.json
        for table in (payload.get("res", {}).get("table_res_list") or []):
            html = str(table.get("pred_html") or "")
            parsed = _parse_html_table(html)
            if parsed is not None:
                candidates.append(parsed)
            else:
                partial = _parse_html_table_partial(html)
                if partial:
                    partial_candidates.append(partial)
                soup = BeautifulSoup(html, "html.parser")
                rejected_tables.append([
                    [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
                    for row in soup.find_all("tr")
                ])

    partial_result = max(partial_candidates, key=len) if partial_candidates else {}
    return (candidates[0] if candidates else None), rejected_tables, partial_result


def _predict_table(
    pipeline: TableRecognitionPipelineV2,
    source_path: str,
):
    return list(pipeline.predict(
        source_path,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_layout_detection=False,
        use_ocr_model=True,
        use_table_orientation_classify=False,
        use_wired_table_cells_trans_to_html=True,
        use_wireless_table_cells_trans_to_html=False,
    ))


def _recognize_table(
    pipeline: TableRecognitionPipelineV2,
    image: Image.Image,
) -> tuple[
    dict[str, dict[str, int]] | None,
    list[list[list[str]]],
    dict[str, dict[str, int]],
    str,
]:
    with tempfile.NamedTemporaryFile(suffix=".png") as source:
        image.save(source.name, format="PNG")
        result, rejected_tables, partial_result = _parse_table_outputs(
            _predict_table(pipeline, source.name)
        )
        mode = "plain" if result is not None else "plain_partial"
        return result, rejected_tables, partial_result, mode


def _emit(marker: str, payload=None) -> None:
    suffix = "" if payload is None else json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    print(marker + suffix, file=PROTOCOL_STDOUT, flush=True)


def _serve() -> int:
    pipeline = _create_pipeline()
    _emit(READY_MARKER)
    for line in sys.stdin:
        request = None
        try:
            request = json.loads(line)
            request_id = str(request["id"])
            image_bytes = base64.b64decode(request["image"], validate=True)
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            result, rejected_tables, partial_result, mode = _recognize_table(pipeline, image)
            response = {"id": request_id, "result": result, "mode": mode}
            if result is None:
                if partial_result:
                    response["partial_result"] = partial_result
                response["error"] = (
                    "incomplete table: "
                    + json.dumps(rejected_tables, ensure_ascii=False, separators=(",", ":"))
                )
            _emit(RESULT_MARKER, response)
        except Exception as exc:
            _emit(RESULT_MARKER, {
                "id": str(request.get("id", "")) if isinstance(request, dict) else "",
                "result": None,
                "error": f"{type(exc).__name__}: {exc}",
            })
    return 0


def main() -> int:
    if "--warmup" in sys.argv[1:]:
        _create_pipeline()
        _emit(READY_MARKER)
        return 0
    if "--serve" in sys.argv[1:]:
        return _serve()
    image = Image.open(BytesIO(sys.stdin.buffer.read())).convert("RGB")
    result, _, _, mode = _recognize_table(_create_pipeline(), image)
    print(f"mode={mode}", file=sys.stderr)
    _emit(RESULT_MARKER, result)
    return 0 if result is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
