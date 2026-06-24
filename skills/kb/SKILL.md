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
  version: "1.4"
  project: knowledge-project-skills
---

## Instructions

### When to activate

Activate when the user invokes `/kb build`, `/kb update`, `/kb add-page`, or
`/kb enrich`, or asks to build, rebuild, update, or enrich the knowledge base
or wiki.

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

#### `enrich`

Retroactive sweep for enrichment gaps that were not resolved inline by `/query`
(e.g. past questions asked before inline enrichment was added, or gaps where
the inline enrichment failed).

Run the automated pipeline:

```
<skill-dir>/scripts/kb_build.py --mode enrich
```

The script outputs:
- Which question files still have `enrichment_needed: true`
- Which sources to re-extract (read from the target pages' frontmatter)
- Which flags were already cleared (target page now has body content)

**After running the script, execute these steps automatically:**

1. For each source ID listed in the script output, invoke the extract skill
   with `--force` on that source.
2. Run `<skill-dir>/scripts/kb_build.py --mode build` to write enriched body
   content into KB pages.
3. Run `<skill-dir>/scripts/kb_build.py --mode enrich` one more time to clear
   the flags on question files whose target pages now have body content.

Report a summary: how many gaps were found, which sources were re-extracted,
how many flags were cleared.

If there are no gaps, say so and stop.

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

### Entity page body

When an extraction includes a `body` field on an entity, the page content is:

1. `context` — the one-liner, written as the lead paragraph under the heading.
2. `body` — the full markdown content (rules, tables, examples) appended after the lead paragraph.

If the same entity has `body` content from multiple sources, each body is rendered
under a `### From <source-id>` sub-heading. Entities with no `body` render the
context one-liner only (unchanged behavior).

---

### Link policy

Links use bare slugs: `[[widget|Widget]]`. Slugs must be globally unique across
all entity subdirectories (`concepts/`, `people/`, `products/`, etc.). Obsidian
resolves `[[slug]]` links by basename; other consumers must implement equivalent
lookup.

If two entities produce the same slug (e.g. "Widget" as both a `product` and a
`concept`), the build disambiguates by appending the entity type:
`widget-product`, `widget-concept`. A warning is printed and the build continues.

---

### Edge cases

- No extractions: print a helpful message, suggest `/extract --all`. Exit cleanly.
- Partial extractions: build from what exists, warn about sources with
  `extraction.status != "complete"` in `.meta.json`. Legacy `extracted: true` is
  treated as complete.
- Broken `[[wikilinks]]`: report as warnings with originating page. Do not fail.
- `schema_version` mismatch in an extraction: skip that source and warn.

---

### References

See [references/kb-schema.md](references/kb-schema.md) for full `index.yaml`
schema and page frontmatter spec.
