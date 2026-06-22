# Spec: kb

**Status**: draft
**Command**: `/kb`
**SKILL.md description**: Build or update the knowledge base in kb/ from extracted content. Use when the user runs /kb, wants to build or rebuild the KB, needs to generate the glossary and wiki pages, or wants to add a manual page to the knowledge base.

---

## Purpose

Generate the full knowledge base from `extractions/` and `kb/questions/`.
Produces the glossary, one Markdown page per entity, and both entry points
(`kb/index.yaml` for agents, `kb/index.md` for Obsidian).

---

## Invocations

```
/kb build                   # full rebuild from all extractions
/kb update                  # rebuild only pages affected by new/changed extractions
/kb add-page <topic>        # create a manual page (generated: false)
```

---

## Internal pipeline (build)

1. **Read** all `extractions/<source-id>.json` files.
2. **Read** `kb/questions/` frontmatter (for feedback signals).
3. **Resolve entities** — merge aliases across extractions, deduplicate.
4. **Write** `kb/glossary.md`.
5. **Write** one `kb/<type>/<topic>.md` per resolved entity.
6. **Write** `kb/index.md` (Obsidian entry point).
7. **Write** `kb/index.yaml` (agent entry point).
8. **Report** any broken `[[wikilinks]]` and `index.yaml` file refs as warnings.

---

## Output

```
kb/
├── index.yaml
├── index.md
├── glossary.md
├── concepts/<topic>.md
├── people/<topic>.md
├── organizations/<topic>.md
├── events/<topic>.md
└── topics/<topic>.md
```

### `kb/index.yaml` schema

```yaml
schema_version: "1"
last_built: "2026-06-21T14:00:00Z"
source_count: 12
entity_count: 84

glossary: glossary.md

pages:
  concepts:
    - title: "Large Language Model"
      file: concepts/large-language-model.md
      aliases: ["LLM", "language model"]
      sources: [src-001, src-004]
  people:
    - title: "Jane Smith"
      file: people/jane-smith.md
      sources: [src-002]
  organizations: []
  events: []
  topics: []

gaps:                           # populated from kb/questions/ low-confidence entries
  - topic: "fine-tuning costs"
    question_count: 3
    max_confidence: low
```

### Entity page frontmatter

```yaml
---
title: Jane Smith
entity_type: person
generated: true
sources:
  - src-002
last_built: 2026-06-21
---
```

Pages with `generated: false` (set by `/kb add-page` or manually) are never
overwritten by `/kb build`.

### `kb/glossary.md` structure

Alphabetically sorted. Each entry:

```markdown
## Jane Smith

**Aliases**: J. Smith

Researcher and lead author of the 2025 report.

**Sources**: [[src-002]]
**Related**: [[Large Language Model]], [[OpenAI]]
```

---

## Feedback from `kb/questions/`

Before writing, `/kb build` reads the frontmatter of all files in
`kb/questions/`. It uses:

- `confidence: low` entries → populate `gaps` in `kb/index.yaml`; these
  signal topics where extractions are thin.
- Frequently occurring topics → promoted to first-class entity pages if not
  already present.
- `answer_sources` trail → informs entity relationship weighting.

---

## Behavior

- **Full rebuild** (`build`): all pages regenerated. Pages with `manual: true`
  or `generated: false` are preserved unchanged.
- **Incremental update** (`update`): only pages whose source extractions have
  changed since `last_built` are regenerated. Faster for large corpora.
- **Broken links**: `[[wikilinks]]` that cannot be resolved are reported as
  warnings, not errors. Build always completes.
- **No extractions**: print helpful message, exit cleanly.
- **Partial extractions**: build from what exists, warn about sources with no
  extraction.

---

## Scripts

Python scripts handle:
- Entity merging and alias resolution across extractions
- Alphabetical glossary generation
- Wikilink resolution and validation
- `kb/index.yaml` generation and schema validation
- File-by-file incremental diffing for `update`
