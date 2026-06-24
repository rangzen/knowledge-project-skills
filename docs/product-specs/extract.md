# Spec: extract

**Status**: draft
**Command**: `/extract`
**SKILL.md description**: Run LLM-based or rule-based extractors over ingested sources and write structured JSON to extractions/. Use when the user runs /extract, wants to process a source, or asks to extract entities, summaries, key facts, or schema from a document.

---

## Purpose

Transform raw sources in `sources/` into structured JSON extractions in
`extractions/`. Each extraction is self-contained and schema-versioned so
downstream skills (`kb`, `query`) can depend on a stable contract.

---

## Invocations

```
/extract <source-id>
/extract --all                          # all sources without an extraction
/extract --all --force                  # re-extract even if extraction exists
/extract --model claude-opus-4-8        # override default model
/extract --all --missing-only           # skip sources with existing extractions
```

---

## Output

One JSON file per source:

```
extractions/
└── <source-id>.json
```

On failure:

```
extractions/
└── <source-id>.failed.json    ← error message + timestamp, never overrides a good extraction
```

### Extraction schema

```json
{
  "schema_version": "1",
  "source_id": "src-001",
  "source_ref": "sources/src-001/report.pdf",
  "extracted_at": "2026-06-21T14:00:00Z",
  "model": "claude-opus-4-8",

  "summary": {
    "short": "One sentence.",
    "long": "Two to five sentences."
  },

  "entities": [
    {
      "name": "Jane Smith",
      "type": "person",
      "aliases": ["J. Smith"],
      "context": "Lead researcher, mentioned in section 2.",
      "source_ref": "sources/src-001/report.pdf"
    }
  ],

  "key_facts": [
    {
      "fact": "Adoption rate increased 40% year-over-year.",
      "source_ref": "sources/src-001/report.pdf",
      "page": 12
    }
  ],

  "dates": [
    {
      "date": "2025-03-15",
      "event": "Report publication",
      "source_ref": "sources/src-001/report.pdf"
    }
  ],

  "schema": null,

  "images": []
}
```

`entity.type` values: `person` | `organization` | `place` | `product` | `concept` | `event` | `other`

For **structured sources** (CSV, DB dump), `schema` is populated:

```json
"schema": {
  "tables": [
    {
      "name": "users",
      "columns": [
        { "name": "id", "type": "integer", "nullable": false },
        { "name": "email", "type": "varchar", "nullable": false }
      ],
      "row_count_estimate": 50000
    }
  ]
}
```

For **PDFs with figures**, `images` is populated:

```json
"images": [
  {
    "page": 7,
    "caption": "Figure 3: Adoption curve 2020–2025",
    "source_ref": "sources/src-001/report.pdf"
  }
]
```

---

## Behavior

- If `extractions/<source-id>.json` already exists and `--force` is not set:
  skip and notify.
- On LLM failure or schema validation error: write `.failed.json` with the
  error. Never leave a partial extraction without marking it failed.
- Large sources are chunked. Chunks are extracted independently and merged.
  Provenance (`source_ref`, `page`) is preserved per chunk.
- `schema_version` in the output must match the version defined in
  `write_extraction.py`. Downstream skills check this field.

---

## Scripts

Python scripts handle:
- PDF text and image extraction (e.g. `pdfplumber`, `pymupdf`)
- CSV/DB schema introspection
- Source chunking for large files
- Output validation against the schema in `write_extraction.py`
- Writing `.failed.json` on error
