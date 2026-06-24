# Spec: ingestion

**Status**: draft
**Command**: `/ingestion`
**SKILL.md description**: Add sources to a knowledge project, check for updates, and track provenance. Use when the user runs /ingestion, wants to add a PDF, URL, CSV, database dump, or any other source file, or needs to check whether existing sources have changed.

---

## Purpose

Manage the `sources/` directory: accept new sources, assign stable IDs, record
provenance, detect changes in previously ingested sources.

---

## Invocations

```
/ingestion add <path-or-url>
/ingestion add <path> --sensitive     # excludes source from git
/ingestion status                     # list all sources and extraction status
/ingestion check-updates              # detect hash changes in existing sources
```

---

## Output

For each ingested source:

```
sources/
└── <source-id>/
      ├── <original-filename>     ← copied/downloaded file
      └── .meta.json              ← provenance record
```

### `.meta.json` schema

```json
{
  "source_id": "src-001",
  "origin": "https://example.com/report.pdf",
  "type": "pdf",
  "ingested_at": "2026-06-21T14:00:00Z",
  "hash": "sha256:<hex>",
  "page_count": 42,
  "sensitive": false,
  "extraction": {"status": "pending"},
  "stale": false
}
```

`type` values: `pdf` | `csv` | `markdown` | `image` | `db-dump` | `text` | `word` | `excel` | `powerpoint` | `odt` | `ods` | `odp` | `other`

---

## Source ID assignment

IDs are stable slugs: `src-<zero-padded-sequence>` (e.g. `src-001`, `src-042`).
The sequence is monotonically increasing per project. IDs are never reused, even
if a source is removed.

---

## Behavior

### `add`
1. Assign a new `source-id`.
2. Copy file to `sources/<source-id>/` or download URL to `sources/<source-id>/`.
3. Compute SHA-256 hash.
4. Write `.meta.json` with `extracted: false`.
5. If `--sensitive`: add `sources/<source-id>/` to `.gitignore`.
6. Print the assigned `source-id` so the user can reference it.

### `status`
List all sources with columns: `source-id`, `type`, `origin`, `ingested-at`,
`extracted` (yes/no), `stale` (yes/no).

### `check-updates`
For each source in `sources/`:
1. Recompute hash of the current file.
2. Compare to stored hash in `.meta.json`.
3. If different: set `stale: true` in `.meta.json`, print warning.
4. For URL sources: re-fetch and compare.

---

## Scripts

Python scripts handle:
- SHA-256 hashing
- URL downloading with redirect following
- PDF page count detection
- `.meta.json` read/write
