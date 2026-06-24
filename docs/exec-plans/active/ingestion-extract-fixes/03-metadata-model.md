# 03 — Metadata Model One-Source-Per-File Invariant

## Problem

`.meta.json` fields (`type`, `hash`, `page_count`) assume a single underlying file. If the model ever drifted toward multi-file sources, these fields would be ambiguous.

## Decision

One source ID always maps to exactly one file. The flat `.meta.json` schema is correct and stays flat.

## Steps

1. Add a comment to `ingest.py` at the source-creation step asserting the invariant:
   - "Each source directory contains exactly one content file."
2. Add a guard in `ingest.py`: if more than one non-hidden, non-meta file is found in `sources/<id>/`, raise a clear error rather than silently reading only the first.
3. Update `SKILL.md` to state the invariant explicitly in the schema section.
4. Add an acceptance test: manually place two files in a source directory and verify `ingest.py` errors out cleanly.

## Acceptance criteria

- `ingest.py` raises a descriptive error if a source directory contains more than one content file.
- `SKILL.md` states the one-source-per-file invariant.
