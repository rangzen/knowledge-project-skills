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
compatibility: Requires Python 3.11+ and uv
metadata:
  version: "1.8"
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
- Skip sources where `extractions/<source-id>.json` already exists unless
  `--force` is set.

**2. For each source, run the two-stage extraction pipeline**

Read `sources/<source-id>/.meta.json` to get `type` and locate the source
file in `sources/<source-id>/`.

**Stage 1 — Preprocess:** give the LLM the best possible input — source
content plus any structural metadata (page count, column names, row count, etc.)
that orients extraction. Three tiers:

**Dedicated scripts** — use these when available:

| Format | Script |
|---|---|
| PDF (`.pdf`) | `uv run <skill-dir>/scripts/preprocess_pdf.py <source-file>` |
| DOCX (`.docx`) | `uv run <skill-dir>/scripts/preprocess_docx.py <source-file>` |
| Excel (`.xlsx`, `.xls`) | `uv run <skill-dir>/scripts/preprocess_excel.py <source-file>` |
| CSV (`.csv`) | `uv run <skill-dir>/scripts/preprocess_csv.py <source-file>` |
| JSON (`.json`) | `uv run <skill-dir>/scripts/preprocess_json.py <source-file>` |
| YAML (`.yaml`, `.yml`) | `uv run <skill-dir>/scripts/preprocess_yaml.py <source-file>` |

Scripts print a JSON payload to stdout:
```json
{"text": "...", "metadata": {"format": "csv", "source_ref": "...", "columns": ["name", "age"], "column_count": 2, "row_count": 150}}
```

**Direct read** — for formats that are already plain text (Markdown, plain text,
Mermaid, and similar). Read the file as-is; no script needed.

**Ad-hoc** — for any other format, do not fail. Attempt to read the file
directly. If the content is not usable as-is, write a small inline script to
extract what is accessible, note what could not be extracted, and proceed with
whatever text is available.

**Stage 2 — Extract (agent):** use the preprocessed text to produce the
extraction JSON by following the prompt template below. This step is
performed by the agent — no separate LLM call is made.

**Stage 3 — Write (script):** validate and persist the extraction JSON.

```
uv run <skill-dir>/scripts/write_extraction.py --source-id <source-id> [--force]
```

Pipe the extraction JSON to this script via stdin (or pass `--input <file>`).
It deduplicates entities, runs quality checks, validates against the schema,
writes `extractions/<source-id>.json`, and updates `.meta.json` with a
structured `extraction` status object. On failure it writes
`extractions/<source-id>.failed.json` and exits non-zero.

---

### Extraction prompt template

Use the source text from the preprocessor output and extract:

```
From the document below, extract the following as a JSON object.

Required fields:
{
  "schema_version": "1",
  "source_id": "<source-id>",
  "source_ref": "<path from metadata>",
  "extracted_at": "<ISO datetime UTC, e.g. 2026-06-24T14:00:00Z>",
  "model": "<model used>",
  "summary": {
    "short": "<one sentence>",
    "long": "<two to five sentences>"
  },
  "entities": [
    {
      "name": "<entity name>",
      "type": "<person|organization|place|product|concept|event|other>",
      "aliases": ["<alternative names>"],
      "context": "<role in this document>",
      "source_ref": "<same as top-level source_ref>"
    }
  ],
  "key_facts": [
    {
      "fact": "<important factual statement>",
      "source_ref": "<same as top-level source_ref>",
      "page": <integer or null>
    }
  ],
  "dates": [
    {
      "date": "<ISO date YYYY-MM-DD or partial like 2025-03>",
      "event": "<what happened>",
      "source_ref": "<same as top-level source_ref>"
    }
  ],
  "schema": null,
  "images": []
}

Rules:
- entities: all significant people, organisations, places, products,
  concepts, and events.
- key_facts: most important claims, findings, or data points.
- dates: all significant dates, ISO format where possible.
- schema: if the document is tabular/structured (CSV, DB dump), populate
  with table/column info instead of null.
- images: if the document references figures, populate with
  {"page": N, "caption": "..."}.

Document format: <format from metadata>
Source reference: <source_ref from metadata>

<document text>
```

For large sources, process in sections and merge results before writing.
Preserve `source_ref` and `page` per fact.

---

### Script reference

#### `preprocess_pdf.py <source-file>`

Extracts text from a PDF with page markers.

Output: `{"text": "...", "metadata": {"format": "pdf", "source_ref": "...", "pages": 10}}`

#### `preprocess_docx.py <source-file>`

Extracts paragraphs and tables from a Word document.

Output: `{"text": "...", "metadata": {"format": "docx", "source_ref": "...", "paragraphs": 42, "tables": 3}}`

#### `preprocess_excel.py <source-file>`

Extracts sheet contents as text tables. Metadata includes sheet count and total row count.

Output: `{"text": "...", "metadata": {"format": "xlsx", "source_ref": "...", "sheets": 2, "rows": 500}}`

#### `preprocess_csv.py <source-file>`

Passes content through unchanged. Extracts column names, column count, row count, and a per-column profile: inferred type (numeric, boolean, text), min/max for numeric columns, and enum values for low-cardinality text columns.

Output: `{"text": "<raw csv>", "metadata": {"format": "csv", "source_ref": "...", "columns": ["name", "age"], "column_count": 2, "row_count": 150, "profile": [...]}}`

#### `preprocess_json.py <source-file>`

Passes content through unchanged. Extracts the structural shape of the document: key names, value types, and array item shapes up to depth 4. Helps the LLM understand the schema before reading the full content.

Output: `{"text": "<raw json>", "metadata": {"format": "json", "source_ref": "...", "shape": {...}}}`

#### `preprocess_yaml.py <source-file>`

Same as `preprocess_json.py` but for YAML files. Parses with `pyyaml` and extracts the same structural shape.

Output: `{"text": "<raw yaml>", "metadata": {"format": "yaml", "source_ref": "...", "shape": {...}}}`

#### `write_extraction.py --source-id <id> [options]`

Deduplicates entities, runs quality checks, validates an agent-produced
extraction JSON (from stdin or `--input`), writes it to
`extractions/<source-id>.json`, and updates `.meta.json` with:
```json
{
  "extraction": {
    "status": "complete",
    "extractor_version": "1.0.0",
    "extracted_at": "<ISO datetime UTC>",
    "quality": "ok | warning | low"
  }
}
```
Migration note: sources with legacy `extracted: true` in `.meta.json` are
treated as `status: "complete", quality: "unknown"` by downstream tools.

| Flag | Effect |
|---|---|
| `--source-id` | (required) source identifier |
| `--input <file>` | read JSON from file instead of stdin |
| `--force` | overwrite if `extractions/<source-id>.json` already exists |

Fails loudly (non-zero exit, `.failed.json` written) on schema errors.

---

### Output schema

`extractions/<source-id>.json` fields:

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | Must be `"1"` |
| `source_id` | string | e.g. `"src-001"` |
| `source_ref` | string | Path to source file |
| `extracted_at` | ISO datetime | UTC, Z suffix |
| `model` | string | Model used |
| `summary.short` | string | One sentence |
| `summary.long` | string | Two to five sentences |
| `entities` | array | See above |
| `key_facts` | array | See above |
| `dates` | array | ISO dates + event description |
| `schema` | object or null | Populated for CSV/DB sources |
| `images` | array | Populated for PDFs with figures |
| `quality.flags` | array of strings | e.g. `["low_entity_count"]` |
| `quality.warnings` | array of strings | Human-readable quality messages |
| `quality.text_coverage` | float or null | Fraction of source text represented |

`quality` is computed and injected by `write_extraction.py` — the agent does not produce it.

The full schema with examples is defined inline in the Output schema section above.

---

### Flags

| Flag | Effect |
|---|---|
| `--all` | Process all un-extracted sources |
| `--force` | Re-extract even if output exists |

---

### Edge cases

- Source not ingested (no `.meta.json`): report error, suggest `/ingestion add`.
- Output already exists and no `--force`: skip and notify.
- `write_extraction.py` writes `.failed.json` on failure; never overwrites a
  good extraction without `--force`.
- `--all` with no un-extracted sources: confirm all sources are up to date.
- Unsupported format: report clearly; do not attempt extraction.
