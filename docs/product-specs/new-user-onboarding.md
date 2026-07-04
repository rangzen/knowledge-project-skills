# New User Onboarding

**Status**: draft

Describes the experience a user should have the first time they use
knowledge-project-skills in a new project.

---

## Goal

A user with a directory of raw documents (PDFs, CSVs, URLs) should be able to
go from zero to a queryable, KB-backed knowledge base in under 10 minutes,
using only agent commands with no manual JSON editing.

---

## Happy path

### Step 1 - Initialize the project

```
/init
```

Creates the directory scaffolding: `sources/`, `staging/`,
`wiki/`, `wiki/queries/`, `.knowledge-project`.

Expected output:
- Confirmation of directories created
- `.knowledge-project` written with project name and schema version
- Agent prints the next suggested command

---

### Step 2 - Add sources

```
/kp-source add ./my-documents/report-2025.pdf
/kp-source add https://example.com/dataset.csv
```

Each call:
- Assigns a stable `<source-id>`
- Copies or downloads the file to `sources/<source-id>/`
- Writes `sources/<source-id>/.meta.json` with origin, hash, ingested-at

```
/kp-source status
```

Lists all sources, their type, and whether they have been extracted yet.

---

### Step 3 - Extract

```
/kp-staging --all
```

Runs the extractor over every source that does not yet have an entry in
`staging/`. Produces one JSON file per source.

For a PDF, the output includes: `entities`, `summary`, `key_facts`, `dates`,
`images`. For a CSV, it includes: `schema`, `summary`, `key_facts`.

---

### Step 4 - Build the knowledge base

```
/kp-wiki build
```

Runs the full KB generation pipeline: merges entity mentions across all
extractions, resolves aliases, writes `wiki/glossary.md`, generates one page per
entity, and produces `wiki/index.md` (Obsidian) and `wiki/index.yaml` (agents).

Open the `wiki/` directory in Obsidian or VS Code with the Foam extension.

---

### Step 5 - Query

```
/kp-query "What are the main findings in the 2025 report?"
```

Returns an answer grounded in the extractions. The question, answer, and a record
of which KB pages / extractions / sources were used (and with what confidence)
are saved to `wiki/queries/2026-06-21-main-findings-2025.md`.

Running `/kp-wiki build` again after accumulating questions will reorganize the KB
around what was actually asked - frequently queried topics become first-class
pages, and low-confidence answers surface as extraction gaps.

---

## Error states to handle gracefully

- `init` called in a directory that already has a `.knowledge-project` file →
  warn and ask for confirmation before overwriting.
- `extract` called with no sources → print helpful message pointing to `ingestion add`.
- `kp-wiki build` called with no extractions → print helpful message pointing to `kp-staging`.
- `kp-wiki build` called with partial extractions → build from what exists, warn about missing sources.

---

## Out of scope for v1

- Multi-user / shared knowledge bases
- Source deduplication across projects
- Incremental KB updates (v1 does a full rebuild)
