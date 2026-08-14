#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["firecrawl-anydoc"]
# ///
"""Anydoc preprocessor: convert any anydoc-supported format to structured
Markdown.

Two roles:
- Primary pass for formats with no dedicated preprocessor: .ppt/.pptx and
  variants, .odt/.ods/.odp, .rtf, .epub.
- Companion pass for Excel and CSV, alongside their dedicated preprocessors
  (preprocess_excel.py, preprocess_csv.py) - see "Multiple staging passes"
  in kp-staging SKILL.md. Write it with `write_extraction.py --suffix anydoc`.

Format is detected from file content, with the extension as fallback.

Usage:
  uv run scripts/preprocess_office.py <source-file>

Outputs a single JSON object to stdout:
  {"text": "...", "metadata": {"format": "pptx", "source_ref": "<path>"}}
"""

import json
import sys
from pathlib import Path

import anydoc


def main():
    if len(sys.argv) != 2:
        print("Usage: preprocess_office.py <source-file>", file=sys.stderr)
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Error: {source_file} not found", file=sys.stderr)
        sys.exit(1)

    data = source_file.read_bytes()
    fmt = anydoc.format_from_bytes(data) or anydoc.format_from_path(str(source_file))
    if not fmt:
        print(f"Error: unrecognized format for {source_file}", file=sys.stderr)
        sys.exit(1)

    try:
        markdown = anydoc.to_markdown_bytes(data, fmt)
    except anydoc.ConvertError as exc:
        print(f"Error: anydoc could not convert {source_file}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "text": markdown,
        "metadata": {
            "format": fmt,
            "source_ref": str(source_file),
        },
    }))


if __name__ == "__main__":
    main()
