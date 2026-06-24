#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx>=1.1"]
# ///
"""DOCX preprocessor: extract text from a Word document and emit LLM-ready JSON.

Usage:
  uv run scripts/preprocess_docx.py <source-file>

Outputs a single JSON object to stdout:
  {"text": "...", "metadata": {"format": "docx", "source_ref": "<path>", "paragraphs": N, "tables": N}}
"""

import json
import sys
from pathlib import Path

import docx


def _table_to_text(table) -> str:
    rows = []
    for row in table.rows:
        rows.append(" | ".join(cell.text.strip() for cell in row.cells))
    return "\n".join(rows)


def main():
    if len(sys.argv) != 2:
        print("Usage: preprocess_docx.py <source-file>", file=sys.stderr)
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Error: {source_file} not found", file=sys.stderr)
        sys.exit(1)

    doc = docx.Document(str(source_file))
    parts: list[str] = []
    para_count = 0

    for block in doc.element.body:
        tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag
        if tag == "p":
            para = docx.text.paragraph.Paragraph(block, doc)
            text = para.text.strip()
            if text:
                parts.append(text)
                para_count += 1
        elif tag == "tbl":
            tbl = docx.table.Table(block, doc)
            parts.append(_table_to_text(tbl))

    table_count = len(doc.tables)

    print(json.dumps({
        "text": "\n\n".join(parts),
        "metadata": {
            "format": "docx",
            "source_ref": str(source_file),
            "paragraphs": para_count,
            "tables": table_count,
        },
    }))


if __name__ == "__main__":
    main()
