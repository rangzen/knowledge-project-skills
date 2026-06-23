---
name: ingestion
description: >
  Add sources to a knowledge project, check for updates, and track provenance.
  Use when the user runs /ingestion, wants to add a PDF, URL, CSV, database dump,
  or any document to sources/, needs to check the status of ingested sources,
  or wants to detect whether a previously ingested source has changed. "kps"
  is the short name for this project (Knowledge Project Skills) — also
  activate when the user says "kps ingestion" or "kps ingest".
compatibility: Requires Python 3.11+
metadata:
  version: "1.0"
  project: knowledge-project-skills
---

## Instructions

### When to activate

Activate when the user invokes `/ingestion add`, `/ingestion status`,
or `/ingestion check-updates`, or asks to add a document or source file
to the project.

---

### Sub-commands

#### `add <path-or-url>`

1. Assign a new `source-id`: read existing IDs from `sources/` and increment
   (`src-001`, `src-002`, …). IDs are never reused.
2. Create `sources/<source-id>/`.
3. Copy the file (or download the URL) into `sources/<source-id>/`.
4. Run `scripts/ingest.py --source-id <source-id> --origin <path-or-url>`:
   - Computes SHA-256 hash.
   - Detects type (`pdf`, `csv`, `url`, `db-dump`, `markdown`, `image`, `other`).
   - Reads page count for PDFs.
   - Writes `sources/<source-id>/.meta.json`.
5. If `--sensitive`: append `sources/<source-id>/` to `.gitignore`.
6. Print the assigned `source-id` and confirm.

`.meta.json` schema:
```json
{
  "source_id": "src-001",
  "origin": "<path-or-url>",
  "type": "pdf",
  "ingested_at": "<ISO datetime>",
  "hash": "sha256:<hex>",
  "page_count": 42,
  "sensitive": false,
  "extracted": false,
  "stale": false
}
```

#### `status`

For each directory in `sources/`, read `.meta.json` and print a table:

| source-id | type | origin | ingested-at | extracted | stale |
|---|---|---|---|---|---|

#### `check-updates`

For each source in `sources/`:
1. Run `scripts/ingest.py --check-update --source-id <source-id>`.
2. The script recomputes the hash (or re-fetches for URLs) and compares to
   the stored hash.
3. If changed: set `stale: true` in `.meta.json` and print a warning.

---

### Flags

| Flag | Effect |
|---|---|
| `--sensitive` | Adds `sources/<source-id>/` to `.gitignore`. |

---

### Edge cases

- URL download fails: report the error, do not create a partial `sources/<source-id>/`.
- File not found: report clearly, suggest checking the path.
- Project not initialized (`.knowledge-project` missing): prompt the user to run `/init` first.
