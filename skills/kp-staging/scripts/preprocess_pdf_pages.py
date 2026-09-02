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

import argparse
import json
import sys
from pathlib import Path

import pypdf

from pdf_ocr import (
    DEFAULT_OCR_CACHE_DIR,
    DEFAULT_OCR_LANGUAGE,
    OcrDependencyError,
    OcrProcessingError,
    OcrSettings,
    create_derivative,
    existing_derivative,
    metadata as ocr_metadata,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract PDF text with page markers.")
    parser.add_argument("source_file")
    parser.add_argument("--ocr", choices=("auto", "off", "force"), default="auto")
    parser.add_argument("--ocr-language", default=DEFAULT_OCR_LANGUAGE)
    parser.add_argument("--ocr-cache-dir", default=DEFAULT_OCR_CACHE_DIR)
    return parser.parse_args()


def main():
    args = parse_args()
    source_file = Path(args.source_file)
    if not source_file.exists():
        print(f"Error: {source_file} not found", file=sys.stderr)
        sys.exit(1)

    try:
        settings = OcrSettings.from_args(args.ocr, args.ocr_language, args.ocr_cache_dir)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    input_file = source_file
    extra_metadata: dict[str, object] = {}
    try:
        derivative = (
            create_derivative(source_file, settings)
            if settings.mode == "force"
            else existing_derivative(source_file, settings)
            if settings.mode == "auto"
            else None
        )
    except (OcrDependencyError, OcrProcessingError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    if derivative is not None:
        input_file, source_hash = derivative[:2]
        extra_metadata = ocr_metadata(input_file, source_hash, settings)

    reader = pypdf.PdfReader(str(input_file))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(f"[Page {i + 1}]\n{text}")

    metadata = {
        "format": "pdf",
        "source_ref": str(source_file),
        "pages": len(reader.pages),
        "paginated": True,
        **extra_metadata,
    }
    print(json.dumps({
        "text": "\n\n".join(pages),
        "metadata": metadata,
    }))


if __name__ == "__main__":
    main()
