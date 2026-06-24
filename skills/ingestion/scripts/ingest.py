#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf>=5.0"]
# ///
"""Ingestion helper: hash sources, detect types, write .meta.json."""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def detect_type(path: Path) -> str:
    suffix = path.suffix.lower()
    mapping = {
        ".pdf": "pdf",
        ".csv": "csv",
        ".md": "markdown",
        ".markdown": "markdown",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".gif": "image",
        ".webp": "image",
        ".sql": "db-dump",
        ".txt": "text",
        # Microsoft Office
        ".doc": "word",
        ".docx": "word",
        ".xls": "excel",
        ".xlsx": "excel",
        ".ppt": "powerpoint",
        ".pptx": "powerpoint",
        # OpenDocument (OpenOffice / LibreOffice)
        ".odt": "odt",
        ".ods": "ods",
        ".odp": "odp",
    }
    return mapping.get(suffix, "other")


def pdf_page_count(path: Path) -> int | None:
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        return len(reader.pages)
    except ImportError:
        pass
    # Fallback: grep /Count in raw bytes
    try:
        import re
        data = path.read_bytes()
        counts = re.findall(rb"/Count\s+(\d+)", data)
        if counts:
            return max(int(c) for c in counts)
    except Exception:
        pass
    return None


def load_existing_hashes(root: Path) -> dict[str, str]:
    """Return mapping of hash -> source_id for all already-ingested sources."""
    existing: dict[str, str] = {}
    sources_dir = root / "sources"
    if not sources_dir.exists():
        return existing
    for meta_file in sources_dir.glob("*/.meta.json"):
        try:
            meta = json.loads(meta_file.read_text())
            if "hash" in meta and "source_id" in meta:
                existing[meta["hash"]] = meta["source_id"]
        except Exception:
            pass
    return existing


def load_existing_names(root: Path) -> dict[str, str]:
    """Return mapping of original filename -> source_id from the origin field of all ingested sources."""
    existing: dict[str, str] = {}
    sources_dir = root / "sources"
    if not sources_dir.exists():
        return existing
    for meta_file in sources_dir.glob("*/.meta.json"):
        try:
            meta = json.loads(meta_file.read_text())
            sid = meta.get("source_id")
            origin = meta.get("origin", "")
            if sid and origin and "://" not in origin:
                existing[Path(origin).name] = sid
        except Exception:
            pass
    return existing


def _primary_content_file(source_dir: Path) -> Path:
    """Return the primary content file in a source directory, oldest by mtime.

    Warns on stderr if multiple files are present (extraction outputs, sidecars, etc.)
    so that the mtime-based selection is visible.
    """
    files = sorted(
        [f for f in source_dir.iterdir() if not f.name.startswith(".")],
        key=lambda f: f.stat().st_mtime,
    )
    if not files:
        print(f"No file found in {source_dir}", file=sys.stderr)
        sys.exit(1)
    if len(files) > 1:
        names = ", ".join(f.name for f in files)
        print(
            f"Warning: {source_dir.name} contains {len(files)} files ({names}); "
            f"using oldest by mtime as primary: {files[0].name}",
            file=sys.stderr,
        )
    return files[0]


def list_directory(directory: Path, root: Path) -> list[dict]:
    """Walk directory recursively; return all non-hidden files with duplicate detection."""
    existing = load_existing_hashes(root)
    records: list[dict] = []

    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for filename in sorted(filenames):
            if filename.startswith("."):
                continue
            filepath = Path(dirpath) / filename
            file_hash = sha256_file(filepath)
            records.append({
                "path": str(filepath),
                "hash": file_hash,
                "type": detect_type(filepath),
                "duplicate_of": existing.get(file_hash),
            })

    return records


def project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".knowledge-project").exists():
            return p
        p = p.parent
    raise SystemExit("No .knowledge-project found. Run /init first.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", default=None)
    parser.add_argument("--origin", default=None)
    parser.add_argument("--check-update", action="store_true")
    parser.add_argument("--list-dir", metavar="DIR", default=None,
                        help="Recursively list supported files with duplicate detection")
    args = parser.parse_args()

    root = project_root()

    if args.list_dir:
        directory = Path(args.list_dir).resolve()
        if not directory.is_dir():
            print(f"Not a directory: {directory}", file=sys.stderr)
            sys.exit(1)
        records = list_directory(directory, root)
        print(json.dumps({
            "directory": str(directory),
            "files": records,
            "total": len(records),
            "duplicates": sum(1 for r in records if r["duplicate_of"]),
        }, indent=2))
        return

    if not args.source_id:
        print("--source-id is required unless --list-dir is used", file=sys.stderr)
        sys.exit(1)

    source_dir = root / "sources" / args.source_id
    meta_path = source_dir / ".meta.json"

    if args.check_update:
        if not meta_path.exists():
            print(f"No .meta.json for {args.source_id}", file=sys.stderr)
            sys.exit(1)
        meta = json.loads(meta_path.read_text())
        file_path = _primary_content_file(source_dir)
        current_hash = sha256_file(file_path)
        if current_hash != meta["hash"]:
            meta["stale"] = True
            meta_path.write_text(json.dumps(meta, indent=2))
            print(f"STALE: {args.source_id} hash changed")
        else:
            print(f"OK: {args.source_id} unchanged")
        return

    file_path = _primary_content_file(source_dir)

    file_type = detect_type(file_path)
    file_hash = sha256_file(file_path)

    existing_hashes = load_existing_hashes(root)
    if file_hash in existing_hashes and existing_hashes[file_hash] != args.source_id:
        print(
            f"Warning: same content already ingested as '{existing_hashes[file_hash]}'",
            file=sys.stderr,
        )
    existing_names = load_existing_names(root)
    if file_path.name in existing_names and existing_names[file_path.name] != args.source_id:
        print(
            f"Warning: filename '{file_path.name}' already ingested as '{existing_names[file_path.name]}'",
            file=sys.stderr,
        )
    page_count = pdf_page_count(file_path) if file_type == "pdf" else None

    meta = {
        "source_id": args.source_id,
        "origin": args.origin or str(file_path),
        "type": file_type,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "hash": file_hash,
        "page_count": page_count,
        "sensitive": False,
        "extraction": {"status": "pending"},
        "stale": False,
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
