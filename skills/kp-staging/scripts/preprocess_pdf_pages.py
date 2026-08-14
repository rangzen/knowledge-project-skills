#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf>=5.0"]
# ///
"""PDF page-exact preprocessor: extract flat text from a PDF with page markers.

Companion pass to preprocess_pdf.py. That pass gives structured Markdown but
no page boundaries; this one gives flat text but an exact [Page N] marker per
page, for extractions that need to cite a page number. Feed both to the agent
as two independent extraction passes - see kp-staging SKILL.md.

Usage:
  uv run scripts/preprocess_pdf_pages.py <source-file>

Outputs a single JSON object to stdout:
  {"text": "...", "metadata": {"format": "pdf", "source_ref": "<path>", "pages": N, "paginated": true}}
"""

import json
import sys
from pathlib import Path

import pypdf


def main():
    if len(sys.argv) != 2:
        print("Usage: preprocess_pdf_pages.py <source-file>", file=sys.stderr)
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
            "paginated": True,
        },
    }))


if __name__ == "__main__":
    main()
