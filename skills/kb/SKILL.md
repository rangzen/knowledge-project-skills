---
name: kb
description: >
  Build or update the knowledge base in kb/ from extracted content. Generates
  kb/glossary.md, one Markdown page per entity, kb/index.md (Obsidian entry
  point), and kb/index.yaml (agent entry point). Reads kb/questions/ feedback
  to prioritize topics and surface extraction gaps. Use when the user runs /kb,
  wants to build or rebuild the KB, needs to generate the glossary or wiki pages,
  or wants to add a manually-curated page to the knowledge base. "kps" is
  the short name for this project (Knowledge Project Skills) — also activate
  when the user says "kps kb".
compatibility: Requires Python 3.11+ and uv
metadata:
  version: "1.2"
  project: knowledge-project-skills
---

## Instructions

### When to activate

Activate when the user invokes `/kb build`, `/kb update`, or `/kb add-page`,
or asks to build, rebuild, or update the knowledge base or wiki.

---

### Sub-commands

#### `build`

Full rebuild from all extractions.

Run:
```
<skill-dir>/scripts/kb_build.py --mode build
```

The script executes this pipeline in order:

1. **Read** all `extractions/<source-id>.json` files. Validate `schema_version`.
2. **Read** frontmatter from all `kb/questions/` files (feedback layer).
3. **Resolve entities** — merge aliases across extractions, deduplicate by
   canonical name.
4. **Write** `kb/glossary.md` — alphabetically sorted, one entry per resolved
   entity with aliases, definition, sources, and `[[wikilinks]]` to related terms.
5. **Write** `kb/<type>/<topic>.md` — one page per entity. Pages with
   `generated: false` or `manual: true` frontmatter are skipped.
6. **Write** `kb/index.md` — Obsidian entry point, pages grouped by entity type.
7. **Write** `kb/index.yaml` — agent entry point (see schema below).
8. **Validate** all `[[wikilinks]]` and `file:` entries in `index.yaml`.
   Report broken links as warnings; never fail the build for broken links.

#### `update`

Incremental rebuild. Only regenerates pages whose source extractions have a
`extracted_at` timestamp newer than the page's `last_built` frontmatter date.

Run:
```
<skill-dir>/scripts/kb_build.py --mode update
```

#### `add-page <topic>`

Create a stub page at `kb/topics/<topic-slug>.md` with `generated: false`
so it is never overwritten by future builds. Open for the user to edit.

---

### `kb/index.yaml` schema

```yaml
schema_version: "1"
last_built: "<ISO datetime>"
source_count: 12
entity_count: 84

glossary: glossary.md

pages:
  concepts:
    - title: "Large Language Model"
      file: concepts/large-language-model.md
      aliases: ["LLM", "language model"]
      sources: [annual-report-2024, prospectus-q1]
  people:
    - title: "Jane Smith"
      file: people/jane-smith.md
      sources: [annual-report-2024]
  organizations: []
  events: []
  topics: []

gaps:
  - topic: "fine-tuning costs"
    question_count: 3
    max_confidence: low
```

`gaps` is populated from `kb/questions/` entries where `confidence` is `low`
or `medium`, grouped by recurring topic keywords.

---

### Entity page frontmatter

```yaml
---
title: Jane Smith
entity_type: person
generated: true
sources:
  - annual-report-2024
last_built: 2026-06-21
---
```

---

### Edge cases

- No extractions: print a helpful message, suggest `/extract --all`. Exit cleanly.
- Partial extractions: build from what exists, warn about sources with
  `extracted: false` in `.meta.json`.
- Broken `[[wikilinks]]`: report as warnings with originating page. Do not fail.
- `schema_version` mismatch in an extraction: skip that source and warn.

---

### References

See [references/kb-schema.md](references/kb-schema.md) for full `index.yaml`
schema and page frontmatter spec.
