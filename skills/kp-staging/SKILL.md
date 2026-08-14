---
name: kp-staging
description: >
  Run LLM-based or rule-based extractors over ingested sources and write
  structured JSON to staging/. Extracts entities, summaries, key facts,
  dates, schema (for structured sources), and images (for PDFs). Use when
  the user runs /kp-staging, wants to process a source, asks to extract entities
  or facts from a document, or needs to populate staging/ before building
  the knowledge base. "kps" is the short name for this project (Knowledge
  Project Skills) - also activate when the user says "kps extract".
compatibility: Requires Python 3.11+ and uv
metadata:
  version: "2.0"
  project: knowledge-project-skills
---

## Instructions

### When to activate

Activate when the user invokes `/kp-staging`, names a specific `source-id` to
process, or asks to extract, analyze, or process a source document.

---

### Steps

**1. Resolve sources to process**

- `<source-id>`: process that one source.
- `--all`: find all `sources/<source-id>/` directories where
  `staging/<source-id>.json` does not exist (or `--force` overrides).
- Skip sources where `staging/<source-id>.json` already exists unless
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
| PDF (`.pdf`) | `uv run <skill-dir>/scripts/preprocess_pdf.py <source-file>` (primary pass — see below for the page-exact companion pass) |
| Word (`.docx`) | `uv run <skill-dir>/scripts/preprocess_docx.py <source-file>` |
| PowerPoint, OpenDocument, RTF, EPUB (`.pptx`, `.ppt`, `.odt`, `.ods`, `.odp`, `.rtf`, `.epub`, and variants) | `uv run <skill-dir>/scripts/preprocess_office.py <source-file>` |
| Excel (`.xlsx`, `.xls`) | `uv run <skill-dir>/scripts/preprocess_excel.py <source-file>` (primary pass — see below for the anydoc companion pass) |
| CSV (`.csv`) | `uv run <skill-dir>/scripts/preprocess_csv.py <source-file>` (primary pass — see below for the anydoc companion pass) |
| JSON (`.json`) | `uv run <skill-dir>/scripts/preprocess_json.py <source-file>` |
| YAML (`.yaml`, `.yml`) | `uv run <skill-dir>/scripts/preprocess_yaml.py <source-file>` |

Scripts print a JSON payload to stdout:
```json
{"text": "...", "metadata": {"format": "csv", "source_ref": "...", "columns": ["name", "age"], "column_count": 2, "row_count": 150}}
```

`preprocess_docx.py`, `preprocess_office.py`, and the primary `preprocess_pdf.py` convert
through [anydoc](https://github.com/firecrawl/anydoc) (`firecrawl-anydoc` on PyPI) into
structured Markdown (real headings, lists, and tables), which extracts far more reliably
than flattened plain text.

**Multiple staging passes** — when two preprocessing strategies for the same source each
capture something the other cannot, run the extraction pipeline once per strategy and write
both, rather than picking one and losing what only the other one has. `write_extraction.py
--suffix <name>` writes `staging/<source-id>.<name>.json` alongside the primary
`staging/<source-id>.json`, without touching `.meta.json` (the primary pass stays the sole
source of truth for extraction status). `/kp-wiki build` merges every `staging/*.json` file
by entity name regardless of how many exist per source, so extra passes need no downstream
wiring.

Three formats use this today, always primary pass unsuffixed + companion pass with `--suffix`:

- **PDF**: anydoc's PDF conversion has no per-page document model (only `to_markdown`, no
  page boundaries), so `preprocess_pdf.py` gives well-structured text with no page numbers.
  Companion: `preprocess_pdf_pages.py` (pypdf, flat text with `[Page N]` markers), written
  with `--suffix pages`, so key facts and dates that need a page citation still get one.
- **Excel**: `preprocess_excel.py` (openpyxl) gives sheet/row metadata and per-sheet tables.
  Companion: `preprocess_office.py` (anydoc), written with `--suffix anydoc`, gives the same
  data through anydoc's Markdown serializer instead, in case its table handling catches
  something the primary pass's cell-by-cell walk does not.
- **CSV**: `preprocess_csv.py` passes the file through unchanged and adds a per-column type
  profile (numeric ranges, enum values). Companion: `preprocess_office.py` (anydoc), written
  with `--suffix anydoc`, gives the same rows as a rendered Markdown table.

Always run every configured companion pass — do not skip one because the primary pass looks
sufficient. The point of this pattern is to never have to judge in advance which pass would
have caught something; run both and let `/kp-wiki build` merge them.

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
uv run <skill-dir>/scripts/write_extraction.py --source-id <source-id> [--force] [--suffix <name>]
```

Pipe the extraction JSON to this script via stdin (or pass `--input <file>`).
It deduplicates entities, runs quality checks, validates against the schema,
writes `staging/<source-id>.json`, and updates `.meta.json` with a
structured `extraction` status object. On failure it writes
`staging/<source-id>.failed.json` and exits non-zero.

For a PDF, Excel, or CSV source, run stages 1-3 twice: once over the primary
preprocessor's output, written with no `--suffix` (this pass owns `.meta.json`
extraction status); once over the companion preprocessor's output (see
"Multiple staging passes" above), written with its `--suffix` (writes
`staging/<source-id>.<suffix>.json`, leaves `.meta.json` untouched). Both get
merged automatically at `/kp-wiki build`.

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
      "context": "<one-sentence role in this document>",
      "body": "<optional markdown — full dedicated content from the source: procedure steps, period description, reference table, diagram transcription, criteria, etc. Omit for shallow entities where context is sufficient.>",
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
  concepts, and events. Also include significant processes, procedures, and
  defined systems — these are just as important as named terms. An entity of
  this kind is significant if it has its own section heading in the source or
  is referenced repeatedly.
- body: for each entity where the source contains substantial dedicated
  content — a procedure, a process, a period description, a reference table,
  a diagram transcription, a configuration reference, a set of criteria — write
  a `body` field with that content in clean markdown. Use headers for
  sub-sections, bullet lists for steps or options, pipe tables for tabular
  data, blockquotes for examples. Omit `body` for shallow entities (a person's
  name, a product citation) where `context` is already complete. The signal
  is: does the source dedicate a section, table, or procedure to this entity?
  If yes, capture it in `body`.
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

Primary PDF pass. Converts to structured Markdown via anydoc (headings, lists,
tables) but carries no page boundaries — anydoc's PDF conversion has no
per-page document model.

Output: `{"text": "...", "metadata": {"format": "pdf", "source_ref": "...", "pages": 10, "paginated": false}}`

#### `preprocess_pdf_pages.py <source-file>`

Page-exact companion pass for PDF. Flat text (pypdf) with a `[Page N]` marker
per page — no heading/table structure, but every fact traces to a page. Feed
this to a second extraction pass and write it with `write_extraction.py
--suffix pages` (see "Multiple staging passes" above).

Output: `{"text": "...", "metadata": {"format": "pdf", "source_ref": "...", "pages": 10, "paginated": true}}`

#### `preprocess_docx.py <source-file>`

Converts a Word document to structured Markdown via anydoc (headings, lists,
tables).

Output: `{"text": "...", "metadata": {"format": "docx", "source_ref": "..."}}`

#### `preprocess_office.py <source-file>`

Converts any anydoc-supported format to structured Markdown. Format is
detected from file content, with the extension as fallback. Two roles:
primary pass for PowerPoint, OpenDocument (`.odt`/`.ods`/`.odp`), RTF, and
EPUB; anydoc companion pass for Excel and CSV, written with `write_extraction.py
--suffix anydoc` (see "Multiple staging passes" above).

Output: `{"text": "...", "metadata": {"format": "pptx", "source_ref": "..."}}`

#### `preprocess_excel.py <source-file>`

Primary Excel pass. Extracts sheet contents as text tables. Metadata includes
sheet count and total row count.

Output: `{"text": "...", "metadata": {"format": "xlsx", "source_ref": "...", "sheets": 2, "rows": 500}}`

#### `preprocess_csv.py <source-file>`

Primary CSV pass. Passes content through unchanged. Extracts column names, column count, row count, and a per-column profile: inferred type (numeric, boolean, text), min/max for numeric columns, and enum values for low-cardinality text columns.

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
`staging/<source-id>.json`, and updates `.meta.json` with:
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

With `--suffix <name>`, writes `staging/<source-id>.<name>.json` instead and
leaves `.meta.json` untouched — for a second independent extraction pass over
the same source (see "Multiple staging passes" above).

| Flag | Effect |
|---|---|
| `--source-id` | (required) source identifier |
| `--input <file>` | read JSON from file instead of stdin |
| `--force` | overwrite if `staging/<source-id>.json` already exists |

Fails loudly (non-zero exit, `.failed.json` written) on schema errors.

---

### Output schema

`staging/<source-id>.json` fields:

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | Must be `"1"` |
| `source_id` | string | e.g. `"src-001"` |
| `source_ref` | string | Path to source file |
| `extracted_at` | ISO datetime | UTC, Z suffix |
| `model` | string | Model used |
| `summary.short` | string | One sentence |
| `summary.long` | string | Two to five sentences |
| `entities` | array | See above. Each entity may include an optional `body` (markdown string) for rich content. |
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

- Source not ingested (no `.meta.json`): report error, suggest `/kp-source add`.
- Output already exists and no `--force`: skip and notify.
- `write_extraction.py` writes `.failed.json` on failure; never overwrites a
  good extraction without `--force`.
- `--all` with no un-extracted sources: confirm all sources are up to date.
- Unsupported format: report clearly; do not attempt extraction.
