# 01 — Directory Ingestion Semantics

## Problem

`ingestion add <path>` does not define behavior for directory input. The bundled `ingest.py` reads only the first non-hidden file in a source directory, silently ignoring siblings.

## Decision

- `ingestion add <directory>` recurses into the directory and ingests each supported file as its own source.
- Source IDs are derived per file (not per directory).
- If the file count in the resolved set exceeds the threshold (default 50, configurable), the skill prints a count and asks for confirmation before creating sources.

## Steps

1. Add a `--threshold` option to `ingest.py` (default 50). Document the option in the skill text.
2. In `ingestion` skill: when `<path>` is a directory, resolve all files recursively (see issue 02 for deduplication).
3. Before creating any sources, count resolved files. If count > threshold, print:
   ```
   Found N files. This will create N sources. Continue? [y/N]
   ```
4. Update `SKILL.md` to document directory input behavior explicitly.
5. Add an acceptance test: directory with 3 files → 3 sources created.
6. Add an acceptance test: directory with 51 files → confirmation prompt appears.

## Acceptance criteria

- `ingestion add <dir>` with 3 files produces 3 distinct sources with correct IDs.
- Exceeding threshold halts and prompts; answering N produces zero sources.
- Passing `--yes` or `--threshold 0` bypasses the prompt for scripted use.
