#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""YAML preprocessor: pass content through and extract structural shape as metadata.

Same shape extraction as preprocess_json.py: key names, value types, and array
item shapes up to depth 4.

Usage:
  uv run scripts/preprocess_yaml.py <source-file>

Outputs a single JSON object to stdout:
  {"text": "<raw yaml>", "metadata": {"format": "yaml", "source_ref": "...", "shape": {...}}}
"""

import json
import sys
from pathlib import Path

import yaml

_MAX_DEPTH = 4
_MAX_KEYS = 30


def _shape(value, depth: int = 0):
    if depth >= _MAX_DEPTH:
        return "..."
    if isinstance(value, dict):
        keys = list(value.keys())[:_MAX_KEYS]
        result = {str(k): _shape(value[k], depth + 1) for k in keys}
        if len(value) > _MAX_KEYS:
            result["..."] = f"({len(value) - _MAX_KEYS} more keys)"
        return result
    if isinstance(value, list):
        if not value:
            return []
        item_shape = _shape(value[0], depth + 1)
        return {"_array_length": len(value), "_item_shape": item_shape}
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if value is None:
        return "null"
    return type(value).__name__


def main():
    if len(sys.argv) != 2:
        print("Usage: preprocess_yaml.py <source-file>", file=sys.stderr)
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Error: {source_file} not found", file=sys.stderr)
        sys.exit(1)

    text = source_file.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    print(json.dumps({
        "text": text,
        "metadata": {
            "format": "yaml",
            "source_ref": str(source_file),
            "shape": _shape(data),
        },
    }))


if __name__ == "__main__":
    main()
