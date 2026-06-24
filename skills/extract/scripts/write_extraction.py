#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate and write an extraction JSON produced by the agent.

Usage:
  echo '<json>' | uv run scripts/write_extraction.py --source-id src-001
  uv run scripts/write_extraction.py --source-id src-001 --input extraction.json
  uv run scripts/write_extraction.py --source-id src-001 --force

Reads the agent-produced extraction JSON from stdin (or --input), validates it
against the schema, writes extractions/<source-id>.json, and sets
extracted: true in sources/<source-id>/.meta.json.

On failure: writes extractions/<source-id>.failed.json and exits non-zero.
Never overwrites a good extraction without --force.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = "1"
VALID_ENTITY_TYPES = {"person", "organization", "place", "product", "concept", "event", "other"}


def project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".knowledge-project").exists():
            return p
        p = p.parent
    raise SystemExit("No .knowledge-project found. Run /init first.")


def validate(data: dict) -> list[str]:
    errors = []

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be '{SCHEMA_VERSION}', got '{data.get('schema_version')}'")

    summary = data.get("summary", {})
    if not isinstance(summary, dict) or not summary.get("short") or not summary.get("long"):
        errors.append("summary must have non-empty 'short' and 'long' strings")

    for i, e in enumerate(data.get("entities", [])):
        if not isinstance(e, dict):
            errors.append(f"entities[{i}] is not an object")
            continue
        if not e.get("name"):
            errors.append(f"entities[{i}] missing 'name'")
        if e.get("type") not in VALID_ENTITY_TYPES:
            errors.append(f"entities[{i}] has invalid type '{e.get('type')}'")

    for i, f in enumerate(data.get("key_facts", [])):
        if not isinstance(f, dict) or not f.get("fact"):
            errors.append(f"key_facts[{i}] missing 'fact'")

    for i, d in enumerate(data.get("dates", [])):
        if not isinstance(d, dict) or not d.get("date") or not d.get("event"):
            errors.append(f"dates[{i}] missing 'date' or 'event'")

    return errors


def write_failure(extractions_dir: Path, source_id: str, error: str) -> None:
    good = extractions_dir / f"{source_id}.json"
    if good.exists():
        return
    failed = extractions_dir / f"{source_id}.failed.json"
    failed.write_text(json.dumps({
        "source_id": source_id,
        "failed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "error": error,
    }, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--input", help="Path to extraction JSON (default: stdin)")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = project_root()
    extractions_dir = root / "extractions"
    extractions_dir.mkdir(exist_ok=True)
    output_path = extractions_dir / f"{args.source_id}.json"

    if output_path.exists() and not args.force:
        print(f"Skipped: extractions/{args.source_id}.json already exists (use --force to re-run).",
              file=sys.stderr)
        sys.exit(0)

    meta_path = root / "sources" / args.source_id / ".meta.json"
    if not meta_path.exists():
        print(f"Error: no .meta.json for {args.source_id}. Run /ingestion add first.",
              file=sys.stderr)
        sys.exit(1)

    raw = Path(args.input).read_text() if args.input else sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"invalid JSON: {exc}"
        print(f"Error: {msg}", file=sys.stderr)
        write_failure(extractions_dir, args.source_id, msg)
        sys.exit(1)

    errors = validate(data)
    if errors:
        msg = "schema validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        print(f"Error: {msg}", file=sys.stderr)
        write_failure(extractions_dir, args.source_id, msg)
        sys.exit(1)

    output_path.write_text(json.dumps(data, indent=2))

    meta = json.loads(meta_path.read_text())
    meta["extracted"] = True
    meta_path.write_text(json.dumps(meta, indent=2))

    entity_count = len(data.get("entities", []))
    print(f"OK: {args.source_id} — {entity_count} entities — {data['summary']['short']}")


if __name__ == "__main__":
    main()
