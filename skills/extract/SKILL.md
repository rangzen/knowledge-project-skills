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
  version: "1.4"
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

**Stage 1 — Preprocess (script):** convert the source file to clean text.

| Format | Preprocessor |
|---|---|
| PDF | `uv run <skill-dir>/scripts/preprocess_pdf.py <source-file>` |
| Markdown / plain text | Read the file directly — no script needed |
| Other formats | (see issue 06 — not yet implemented) |

The preprocessor prints a JSON payload to stdout:
```json
{"text": "...", "metadata": {"format": "pdf", "source_ref": "sources/src-001/file.pdf", "pages": 10}}
```

For unsupported formats, report the error to the user rather than attempting
extraction.

**Stage 2 — Extract (agent):** use the preprocessed text to produce the
extraction JSON by following the prompt template below. This step is
performed by the agent — no separate LLM call is made.

**Stage 3 — Write (script):** validate and persist the extraction JSON.

```
uv run <skill-dir>/scripts/write_extraction.py --source-id <source-id> [--force]
```

Pipe the extraction JSON to this script via stdin (or pass `--input <file>`).
It validates the output against the schema, writes
`extractions/<source-id>.json`, and sets `extracted: true` in `.meta.json`.
On failure it writes `extractions/<source-id>.failed.json` and exits
non-zero.

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

Reads a PDF and emits a JSON payload on stdout. No side effects.

```
uv run <skill-dir>/scripts/preprocess_pdf.py sources/src-001/report.pdf
```

Output:
```json
{"text": "...", "metadata": {"format": "pdf", "source_ref": "sources/src-001/report.pdf", "pages": 10}}
```

#### `write_extraction.py --source-id <id> [options]`

Validates an agent-produced extraction JSON (from stdin or `--input`) and
writes it to `extractions/<source-id>.json`. Updates `.meta.json`.

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
