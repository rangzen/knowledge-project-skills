#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf>=5.0", "firecrawl-anydoc"]
# ///
"""PDF preprocessor: convert a PDF to structured Markdown via anydoc.

This is the primary PDF pass - it preserves headings, lists, and tables,
but anydoc gives no per-page boundaries for PDF (its document model does
not cover PDF, only to_markdown does). For page-exact facts, run the
companion pass: preprocess_pdf_pages.py.

Usage:
  uv run scripts/preprocess_pdf.py <source-file>

Outputs a single JSON object to stdout:
  {"text": "...", "metadata": {"format": "pdf", "source_ref": "<path>", "pages": N, "paginated": false}}
"""

import json
import sys
from pathlib import Path

import anydoc
import pypdf


def main():
    if len(sys.argv) != 2:
        print("Usage: preprocess_pdf.py <source-file>", file=sys.stderr)
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Error: {source_file} not found", file=sys.stderr)
        sys.exit(1)

    page_count = len(pypdf.PdfReader(str(source_file)).pages)

    try:
        markdown = anydoc.to_markdown(str(source_file))
    except anydoc.ConvertError as exc:
        print(f"Error: anydoc could not convert {source_file}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "text": markdown,
        "metadata": {
            "format": "pdf",
            "source_ref": str(source_file),
            "pages": page_count,
            "paginated": False,
        },
    }))


if __name__ == "__main__":
    main()
