"""Import lesson text arrays from the upstream eelll/JS data file.

Usage: python import_eelll_texts.py SOURCE_JS OUTPUT_JSON
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


TARGETS = set(range(5, 26)) | set(range(101, 107))


def parse(source: str) -> dict[int, list[str]]:
    records: dict[int, list[str]] = {}
    pattern = re.compile(
        r'\{\s*name:\s*"(\d+)"\s*,.*?text:\s*\[(.*?)\]\s*\}',
        re.DOTALL,
    )
    for number_text, text_body in pattern.findall(source):
        number = int(number_text)
        if number not in TARGETS:
            continue
        lines = [json.loads(item) for item in re.findall(r'"(?:\\.|[^"\\])*"', text_body)]
        if lines:
            records[number] = lines
    missing = sorted(TARGETS - records.keys())
    if missing:
        raise ValueError(f"missing lesson text: {missing}")
    return records


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: import_eelll_texts.py SOURCE_JS OUTPUT_JSON")
    source_path, output_path = map(Path, sys.argv[1:])
    records = parse(source_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({str(key): value for key, value in sorted(records.items())},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
