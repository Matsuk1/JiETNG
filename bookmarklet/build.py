#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "maimai-session-exporter.js"
DIST = ROOT / "dist"
OUTPUT = DIST / "bookmarklet.txt"
DOCS_OUTPUT = ROOT.parent / "docs" / "public" / "bookmarklet" / "maimai-session-image.txt"


def main() -> None:
    DIST.mkdir(exist_ok=True)
    code = SOURCE.read_text(encoding="utf-8").strip()
    bookmarklet = "javascript:" + quote(code, safe="()[]{}!~*'._-;,/:?@&=+$#%")
    OUTPUT.write_text(bookmarklet, encoding="utf-8")
    DOCS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DOCS_OUTPUT.write_text(bookmarklet, encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"Wrote {DOCS_OUTPUT}")


if __name__ == "__main__":
    main()
