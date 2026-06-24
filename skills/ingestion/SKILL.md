---
name: ingestion
description: >
  Add sources to a knowledge project, check for updates, and track provenance.
  Use when the user runs /ingestion, wants to add a PDF, URL, CSV, database dump,
  or any document to sources/, needs to check the status of ingested sources,
  or wants to detect whether a previously ingested source has changed. "kps"
  is the short name for this project (Knowledge Project Skills) — also
  activate when the user says "kps ingestion" or "kps ingest".
compatibility: Requires Python 3.11+ and uv
metadata:
  version: "1.3"
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

**If `<path>` is a directory:**

1. Run `<skill-dir>/scripts/ingest.py --list-dir <path>` to discover files.
   The script walks recursively (skipping hidden files and dirs), hashes each
   file, and checks against existing sources for duplicates. All file types
   are included — no extension filtering.
2. Count files where `duplicate_of` is `null` (new files to ingest).
3. If that count exceeds the threshold (default 50, override with `--threshold N`):
   ```
   Found N files. This will create N sources. Continue? [y/N]
   ```
   If the user answers N (or gives no answer), abort with zero sources created.
   Pass `--yes` to skip this prompt for scripted use (`--threshold 0` also bypasses it).
4. For each non-duplicate file, run the single-file ingestion steps below
   (derive slug, create directory, copy, run ingest.py, handle `--sensitive`).
5. After all files are processed, print a summary:
   ```
   Added:      N
   Duplicate:  N  (already ingested as <source-id>)
   Failed:     N
   ```

**If `<path>` is a single file or a URL:**

1. Assign a `source-id` slug:
   - Derive a short kebab-case slug from the filename or URL
     (e.g. `cairn-annual-report`, `privacy-policy-2024`).
   - Keep it concise: 2–4 meaningful words, lowercase, hyphens only.
   - Check uniqueness against existing directory names in `sources/`.
   - If the slug already exists, append `-2`, `-3`, etc. until unique.
2. Create `sources/<source-id>/`.
3. Copy the file (or download the URL) into `sources/<source-id>/`.
4. Run `<skill-dir>/scripts/ingest.py --source-id <source-id> --origin <path-or-url>`:
   - Computes SHA-256 hash.
   - Detects type (`pdf`, `csv`, `url`, `db-dump`, `markdown`, `image`, `other`).
   - Reads page count for PDFs.
   - Writes `sources/<source-id>/.meta.json`.
5. If `--sensitive`: append `sources/<source-id>/` to `.gitignore`.
6. Print the assigned `source-id` and confirm.

`.meta.json` schema:
```json
{
  "source_id": "generated-source-slug",
  "origin": "<path-or-url>",
  "type": "pdf",
  "ingested_at": "<ISO datetime>",
  "hash": "sha256:<hex>",
  "page_count": 42,
  "sensitive": false,
  "extraction": {"status": "pending"},
  "stale": false
}
```
#### `status`

For each directory in `sources/`, read `.meta.json` and print a table:

| source-id | type | origin | ingested-at | extraction.status | stale |
|---|---|---|---|---|---|

#### `check-updates`

For each source in `sources/`:
1. Run `<skill-dir>/scripts/ingest.py --check-update --source-id <source-id>`.
2. The script recomputes the hash (or re-fetches for URLs) and compares to
   the stored hash.
3. If changed: set `stale: true` in `.meta.json` and print a warning.

---

### Flags

| Flag | Effect |
|---|---|
| `--sensitive` | Adds `sources/<source-id>/` to `.gitignore`. |
| `--threshold N` | Override the file-count confirmation threshold (default 50). Set to 0 to disable. |
| `--yes` | Skip the directory file-count confirmation prompt. |

---

### Edge cases

- URL download fails: report the error, do not create a partial `sources/<source-id>/`.
- File not found: report clearly, suggest checking the path.
- Project not initialized (`.knowledge-project` missing): prompt the user to run `/init` first.
- Empty directory: report zero files found.
- Duplicate file in directory input: log it in the summary (`Duplicate: N`) with the existing `source-id`; do not re-ingest.
