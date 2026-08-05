"""Regenerate the static Traditional Chinese message catalog."""

from pathlib import Path
from pprint import pformat
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from languages.zh import MESSAGE_TEXTS  # noqa: E402
from modules.zh_tw import to_traditional  # noqa: E402


START = "# BEGIN GENERATED MESSAGE TEXTS"
END = "# END GENERATED MESSAGE TEXTS"


def traditionalize(value):
    if isinstance(value, str):
        return to_traditional(value)
    if isinstance(value, dict):
        return {key: traditionalize(item) for key, item in value.items()}
    return value


def main():
    path = ROOT / "languages" / "zh_tw.py"
    source = path.read_text(encoding="utf-8")
    before, rest = source.split(START, 1)
    _, after = rest.split(END, 1)
    catalog = pformat(traditionalize(MESSAGE_TEXTS), sort_dicts=True, width=100)
    generated = f"{START}\nMESSAGE_TEXTS = {catalog}\n{END}"
    path.write_text(before + generated + after, encoding="utf-8")


if __name__ == "__main__":
    main()
