#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["firecrawl-anydoc"]
# ///
"""DOCX preprocessor: convert a Word document to structured Markdown via anydoc.

Usage:
  uv run scripts/preprocess_docx.py <source-file>

Outputs a single JSON object to stdout:
  {"text": "...", "metadata": {"format": "docx", "source_ref": "<path>"}}
"""

import json
import sys
from pathlib import Path

import anydoc


def main():
    if len(sys.argv) != 2:
        print("Usage: preprocess_docx.py <source-file>", file=sys.stderr)
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Error: {source_file} not found", file=sys.stderr)
        sys.exit(1)

    try:
        markdown = anydoc.to_markdown(str(source_file))
    except anydoc.ConvertError as exc:
        print(f"Error: anydoc could not convert {source_file}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "text": markdown,
        "metadata": {
            "format": "docx",
            "source_ref": str(source_file),
        },
    }))


if __name__ == "__main__":
    main()
