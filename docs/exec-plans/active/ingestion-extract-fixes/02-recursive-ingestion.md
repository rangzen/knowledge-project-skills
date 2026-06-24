# 02 — Recursive Ingestion + Duplicate Handling

## Problem

The initial scan only covered shallow files. Nested directories were missed, producing incomplete ingestion of real document sets (e.g. `Mycronics Manuals/` with 5 subdirectories).

Duplicate files across directories are also undetected.

## Decision

- Recursion is the default for directory input. No `--recursive` flag needed.
- Duplicate detection uses content hash. Duplicates are logged but not ingested again; they are listed in the summary report.

## Steps

1. In the directory resolution step (see issue 01), use `os.walk` or equivalent to collect all files under the root.
2. Filter to supported extensions (see issue 06 for the supported format list).
3. Before ingesting each file, check its SHA-256 hash against existing sources:
   - If hash matches an existing source, skip and log as duplicate.
4. After ingestion, print a summary:
   ```
   Added:      12
   Skipped:    3  (unsupported format)
   Duplicate:  2  (already ingested as <source-id>)
   Failed:     0
   ```
5. Add an acceptance test: two identical files in different subdirectories → one ingested, one logged as duplicate.

## Acceptance criteria

- Nested directories are discovered recursively without a flag.
- Duplicate files (same hash) produce exactly one source; the other is logged with a reference to the existing source ID.
- Summary report is printed after every directory ingestion run.
