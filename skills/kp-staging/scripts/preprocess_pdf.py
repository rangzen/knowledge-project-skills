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

import argparse
import json
import sys
from pathlib import Path

import anydoc
import pypdf

from pdf_ocr import (
    DEFAULT_OCR_CACHE_DIR,
    DEFAULT_OCR_LANGUAGE,
    OcrDependencyError,
    OcrProcessingError,
    OcrSettings,
    create_derivative,
    metadata as ocr_metadata,
    ocr_required,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a PDF to structured Markdown.")
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

    page_count = len(pypdf.PdfReader(str(source_file)).pages)
    try:
        settings = OcrSettings.from_args(args.ocr, args.ocr_language, args.ocr_cache_dir)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    input_file = source_file
    extra_metadata: dict[str, object] = {}
    if settings.mode == "force":
        try:
            input_file, source_hash, _ = create_derivative(source_file, settings)
        except (OcrDependencyError, OcrProcessingError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        extra_metadata = ocr_metadata(input_file, source_hash, settings)

    try:
        markdown = anydoc.to_markdown(str(input_file))
    except anydoc.ConvertError as exc:
        if settings.mode == "off" or not ocr_required(exc):
            print(f"Error: anydoc could not convert {source_file}: {exc}", file=sys.stderr)
            sys.exit(1)
        try:
            input_file, source_hash, _ = create_derivative(source_file, settings)
            markdown = anydoc.to_markdown(str(input_file))
            extra_metadata = ocr_metadata(input_file, source_hash, settings)
        except (OcrDependencyError, OcrProcessingError) as ocr_exc:
            print(
                f"Error: anydoc requires OCR for {source_file}: {exc}\n"
                f"OCR fallback failed: {ocr_exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        except anydoc.ConvertError as retry_exc:
            print(
                f"Error: anydoc requires OCR for {source_file}: {exc}\n"
                f"AnyDoc still failed after local OCR: {retry_exc}",
                file=sys.stderr,
            )
            sys.exit(1)

    metadata = {
        "format": "pdf",
        "source_ref": str(source_file),
        "pages": page_count,
        "paginated": False,
        **extra_metadata,
    }
    print(json.dumps({
        "text": markdown,
        "metadata": metadata,
    }))


if __name__ == "__main__":
    main()
