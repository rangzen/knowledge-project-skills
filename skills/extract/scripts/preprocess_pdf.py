#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf>=5.0"]
# ///
"""PDF preprocessor: extract text from a PDF and emit LLM-ready JSON.

Usage:
  uv run scripts/preprocess_pdf.py <source-file>

Outputs a single JSON object to stdout:
  {"text": "...", "metadata": {"format": "pdf", "source_ref": "<path>", "pages": N}}
"""

import json
import sys
from pathlib import Path

import pypdf


def main():
    if len(sys.argv) != 2:
        print("Usage: preprocess_pdf.py <source-file>", file=sys.stderr)
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Error: {source_file} not found", file=sys.stderr)
        sys.exit(1)

    reader = pypdf.PdfReader(str(source_file))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(f"[Page {i + 1}]\n{text}")

    print(json.dumps({
        "text": "\n\n".join(pages),
        "metadata": {
            "format": "pdf",
            "source_ref": str(source_file),
            "pages": len(reader.pages),
        },
    }))


if __name__ == "__main__":
    main()
