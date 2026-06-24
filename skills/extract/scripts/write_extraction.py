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

Reads the agent-produced extraction JSON from stdin (or --input), deduplicates
entities, runs quality checks, validates against the schema, writes
extractions/<source-id>.json, and updates sources/<source-id>/.meta.json with
a structured extraction status object.

On failure: writes extractions/<source-id>.failed.json and exits non-zero.
Never overwrites a good extraction without --force.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = "1"
EXTRACTOR_VERSION = "1.0.0"
VALID_ENTITY_TYPES = {"person", "organization", "place", "product", "concept", "event", "other"}
MIN_SUMMARY_LENGTH = 50
MIN_ENTITY_COUNT = 2


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


def deduplicate_entities(entities: list[dict]) -> tuple[list[dict], int]:
    """Return (unique entities, count of duplicates removed). Keyed by normalised name."""
    seen: set[str] = set()
    unique: list[dict] = []
    for entity in entities:
        key = entity.get("name", "").lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(entity)
    return unique, len(entities) - len(unique)


def quality_check(data: dict) -> dict:
    """Compute quality flags for an extraction. Returns the quality block dict."""
    flags: list[str] = []
    warnings: list[str] = []

    summary_short = data.get("summary", {}).get("short", "")
    entities = data.get("entities", [])
    facts = data.get("key_facts", [])

    if len(summary_short) < MIN_SUMMARY_LENGTH and not entities and not facts:
        flags.append("no_text")
        warnings.append("No usable text extracted; source may be empty or unsupported.")
    else:
        if len(summary_short) < MIN_SUMMARY_LENGTH:
            flags.append("low_summary")
            warnings.append(f"Summary is shorter than {MIN_SUMMARY_LENGTH} characters.")
        if len(entities) < MIN_ENTITY_COUNT:
            flags.append("low_entity_count")
            count = len(entities)
            noun = "entity" if count == 1 else "entities"
            warnings.append(f"Only {count} {noun} extracted; expected at least {MIN_ENTITY_COUNT}.")

    return {"flags": flags, "warnings": warnings, "text_coverage": None}


def quality_level(quality: dict) -> str:
    flags = quality.get("flags", [])
    if not flags:
        return "ok"
    if "no_text" in flags or len(flags) >= 2:
        return "low"
    return "warning"


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

    data["entities"], removed = deduplicate_entities(data.get("entities", []))

    quality = quality_check(data)
    data["quality"] = quality

    output_path.write_text(json.dumps(data, indent=2))

    extracted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    meta = json.loads(meta_path.read_text())
    meta.pop("extracted", None)
    meta["extraction"] = {
        "status": "complete",
        "extractor_version": EXTRACTOR_VERSION,
        "extracted_at": extracted_at,
        "quality": quality_level(quality),
    }
    meta_path.write_text(json.dumps(meta, indent=2))

    entity_count = len(data["entities"])
    print(f"OK: {args.source_id} — {entity_count} entities — {data['summary']['short']}")
    if removed:
        print(f"  Deduplication: removed {removed} duplicate {'entity' if removed == 1 else 'entities'}")
    if quality["flags"]:
        for w in quality["warnings"]:
            print(f"  Warning: {w}")
        print(f"  Quality: {quality_level(quality)} (flags: {', '.join(quality['flags'])})")


if __name__ == "__main__":
    main()
