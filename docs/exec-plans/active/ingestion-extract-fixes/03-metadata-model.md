# 03 — Metadata Model: Primary File Selection and Duplicate Warnings

## Problem

`.meta.json` fields (`type`, `hash`, `page_count`) are defined relative to one primary
content file per source. `ingest.py` was using `files[0]` which is non-deterministic
when a source directory contains multiple files (extraction outputs, sidecars, etc.).

No duplicate check existed on the single-file ingestion path (only `--list-dir` had it).

## Decision

- A source directory may contain multiple files (the original content file plus extraction
  outputs or other sidecars produced later). The primary content file is the oldest by mtime,
  which is the original ingested file.
- Duplicate detection (by hash and by filename) warns but does not block ingestion.

## What was implemented

1. `_primary_content_file(source_dir)` — sorts non-hidden files by mtime ascending, picks
   the oldest, warns on stderr if multiple files are present.
2. Both `--check-update` and the main ingestion path now go through this helper.
3. On the main ingestion path: after hashing, compare against `load_existing_hashes` (same
   content already ingested elsewhere) and `load_existing_names` (same original filename
   already ingested elsewhere). Both emit a warning but do not abort.

## Acceptance criteria (met)

- Multiple files in a source directory: no error, oldest by mtime is used, warning printed.
- Duplicate hash: warning on stderr.
- Duplicate filename: warning on stderr.
