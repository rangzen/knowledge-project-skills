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
compatibility: Requires Python 3.11+
metadata:
  version: "1.0"
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

```
scripts/extract.py --source-id <source-id> [--model <model>]
```

The script:
1. Reads `sources/<source-id>/.meta.json` to determine type.
2. Parses the source file (PDF text, CSV rows, URL content, etc.).
3. Chunks large sources and extracts each chunk independently.
4. Calls the LLM at temperature=0 to extract structured data.
5. Validates output against the extraction schema.
6. Writes `extractions/<source-id>.json`.
7. Sets `extracted: true` in `sources/<source-id>/.meta.json`.
8. On failure: writes `extractions/<source-id>.failed.json` with the error
   and timestamp. Never overwrites a successful extraction with a failure.

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
| `--model <id>` | Override default model (default: `claude-sonnet-4-6`) |
| `--missing-only` | Same as `--all` without `--force` (default behavior) |

---

### Edge cases

- Source not ingested (no `.meta.json`): report error, suggest `/ingestion add`.
- LLM context limit exceeded: the script chunks the source automatically.
- Schema validation fails: write `.failed.json`, do not write a partial JSON.
- `--all` with no un-extracted sources: confirm to the user that all sources
  are up to date.
