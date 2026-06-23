#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf>=5.0"]
# ///
"""PDF text extractor: parse a PDF source and print its text for Claude to process.

Usage:
  uv run scripts/extract_pdf.py --source-id src-001
  uv run scripts/extract_pdf.py --source-id src-001 --force

Prints a JSON header line then ---TEXT--- then the full page-by-page text.
Exits 0 with a "Skipped" message if already extracted and --force is not set.
"""

import argparse
import json
import sys
from pathlib import Path

import pypdf


def project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".knowledge-project").exists():
            return p
        p = p.parent
    raise SystemExit("No .knowledge-project found. Run /init first.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = project_root()
    source_dir = root / "sources" / args.source_id
    meta_path = source_dir / ".meta.json"
    extraction_path = root / "extractions" / f"{args.source_id}.json"

    if not meta_path.exists():
        print(f"Error: no .meta.json for {args.source_id}. Run /ingestion add first.", file=sys.stderr)
        sys.exit(1)

    meta = json.loads(meta_path.read_text())

    if meta.get("extracted") and not args.force:
        print(f"Skipped: {args.source_id} already extracted (use --force to re-run).", file=sys.stderr)
        sys.exit(0)

    if extraction_path.exists() and not args.force:
        print(f"Skipped: extractions/{args.source_id}.json exists (use --force to re-run).", file=sys.stderr)
        sys.exit(0)

    pdf_files = [f for f in source_dir.iterdir() if f.suffix.lower() == ".pdf"]
    if not pdf_files:
        print(f"Error: no PDF file found in {source_dir}", file=sys.stderr)
        sys.exit(1)
    source_file = pdf_files[0]

    reader = pypdf.PdfReader(str(source_file))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(f"[Page {i + 1}]\n{text}")

    print(json.dumps({"source_id": args.source_id, "source_ref": str(source_file), "type": "pdf"}))
    print("---TEXT---")
    print("\n\n".join(pages))


if __name__ == "__main__":
    main()
