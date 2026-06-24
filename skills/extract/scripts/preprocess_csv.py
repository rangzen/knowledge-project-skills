#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""CSV preprocessor: pass content through and extract column structure and data profile.

Metadata extracted per column:
  - inferred type (numeric, boolean, date, text)
  - for numeric columns: min, max
  - for low-cardinality text columns: enum values (distinct values)

Usage:
  uv run scripts/preprocess_csv.py <source-file>

Outputs a single JSON object to stdout:
  {"text": "<raw csv>", "metadata": {"format": "csv", "source_ref": "...", "columns": [...], "row_count": N, "profile": {...}}}
"""

import csv
import json
import sys
from pathlib import Path

_ENUM_MAX_DISTINCT = 20
_ENUM_MAX_RATIO = 0.5
_BOOL_VALUES = {"true", "false", "yes", "no", "1", "0", "t", "f", "y", "n"}


def _infer_type(values: list[str]) -> str:
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return "empty"
    if all(v.lower() in _BOOL_VALUES for v in non_empty):
        return "boolean"
    try:
        for v in non_empty:
            float(v)
        return "numeric"
    except ValueError:
        pass
    return "text"


def _profile_column(name: str, values: list[str], row_count: int) -> dict:
    col: dict = {"name": name, "type": _infer_type(values)}
    non_empty = [v for v in values if v.strip()]
    col["null_count"] = len(values) - len(non_empty)

    if col["type"] == "numeric" and non_empty:
        nums = [float(v) for v in non_empty]
        col["min"] = min(nums)
        col["max"] = max(nums)
    elif col["type"] == "text" and non_empty:
        distinct = list(dict.fromkeys(non_empty))
        if len(distinct) <= _ENUM_MAX_DISTINCT and len(distinct) <= max(1, row_count * _ENUM_MAX_RATIO):
            col["enum"] = distinct

    return col


def main():
    if len(sys.argv) != 2:
        print("Usage: preprocess_csv.py <source-file>", file=sys.stderr)
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Error: {source_file} not found", file=sys.stderr)
        sys.exit(1)

    with source_file.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        rows = list(reader)

    if not rows:
        print(json.dumps({"text": "", "metadata": {"format": "csv", "source_ref": str(source_file), "columns": [], "column_count": 0, "row_count": 0, "profile": []}}))
        return

    header = rows[0]
    data_rows = rows[1:]
    row_count = len(data_rows)

    profile = []
    for i, name in enumerate(header):
        col_values = [row[i] if i < len(row) else "" for row in data_rows]
        profile.append(_profile_column(name, col_values, row_count))

    print(json.dumps({
        "text": source_file.read_text(encoding="utf-8"),
        "metadata": {
            "format": "csv",
            "source_ref": str(source_file),
            "columns": header,
            "column_count": len(header),
            "row_count": row_count,
            "profile": profile,
        },
    }))


if __name__ == "__main__":
    main()
