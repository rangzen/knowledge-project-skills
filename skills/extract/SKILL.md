---
name: extract
description: >
  Run LLM-based or rule-based extractors over ingested sources and write
  structured JSON to extractions/. Extracts entities, summaries, key facts,
  dates, schema (for structured sources), and images (for PDFs). Use when
  the user runs /extract, wants to process a source, asks to extract entities
  or facts from a document, or needs to populate extractions/ before building
  the knowledge base. "kps" is the short name for this project (Knowledge
  Project Skills) — also activate when the user says "kps extract".
compatibility: Requires Python 3.11+ and uv (for PDF sources only)
metadata:
  version: "1.2"
  project: knowledge-project-skills
---

## Instructions

### When to activate

Activate when the user invokes `/extract`, names a specific `source-id` to
process, or asks to extract, analyze, or process a source document.

---

### Steps

**1. Resolve sources to process**

- `<source-id>`: process that one source.
- `--all`: find all `sources/<source-id>/` directories where
  `extractions/<source-id>.json` does not exist (or `--force` overrides).
- Skip sources with `.meta.json` `extracted: true` unless `--force` is set.

**2. For each source, run the extraction pipeline**

Read `sources/<source-id>/.meta.json` to determine the source type, then:

**For PDF sources** — use the bundled helper to extract the text:

```
uv run <skill-dir>/scripts/extract_pdf.py --source-id <source-id> [--force]
```

The script prints a JSON header line (`source_id`, `source_ref`, `type`) then
`---TEXT---` then the full page-by-page text. Use the text after `---TEXT---`
as input to the extraction step below.

**For all other source types** — read the source file directly from
`sources/<source-id>/`.

**Extract structured data:**

Use the source content to produce the extraction JSON (schema below).
For large sources, process in sections but produce a single merged JSON.

**Write the results:**

1. Write `extractions/<source-id>.json`.
2. Set `extracted: true` in `sources/<source-id>/.meta.json`.
3. On failure: do not write a partial JSON. Report the error to the user.

**3. Report results**

Print per-source: success / failure / skipped, and for successes the entity
count and a one-line summary.

---

### Output schema

`extractions/<source-id>.json` fields:

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | Must be `"1"` |
| `source_id` | string | e.g. `"src-001"` |
| `source_ref` | string | Path to source file |
| `extracted_at` | ISO datetime | |
| `model` | string | Model used |
| `summary.short` | string | One sentence |
| `summary.long` | string | Two to five sentences |
| `entities` | array | See below |
| `key_facts` | array | See below |
| `dates` | array | ISO dates + event description |
| `schema` | object or null | Populated for CSV/DB sources |
| `images` | array | Populated for PDFs with figures |

Entity fields: `name`, `type`, `aliases`, `context`, `source_ref`.
Entity types: `person` `organization` `place` `product` `concept` `event` `other`.

Key fact fields: `fact`, `source_ref`, `page` (optional).

See [references/extraction-schema.md](references/extraction-schema.md) for the
full schema with examples.

---

### Flags

| Flag | Effect |
|---|---|
| `--all` | Process all un-extracted sources |
| `--force` | Re-extract even if `extractions/<source-id>.json` exists |
| `--missing-only` | Same as `--all` without `--force` (default behavior) |

---

### Edge cases

- Source not ingested (no `.meta.json`): report error, suggest `/ingestion add`.
- Script exits 0 with "Skipped" message (already extracted, no `--force`): treat as success, move on.
- `extract_pdf.py` not found: the script ships with the extract skill at `scripts/extract_pdf.py` relative to this SKILL.md.
- Non-PDF source: do not call the script; read the file directly.
- `--all` with no un-extracted sources: confirm to the user that all sources are up to date.
