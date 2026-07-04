# Spec: wiki

**Status**: draft
**Command**: `/kp-wiki`
**SKILL.md description**: Build or update the wiki in wiki/ from staged content. Use when the user runs /kp-wiki, wants to build or rebuild the wiki, needs to generate the glossary and wiki pages, or wants to add a manual page to the wiki.

---

## Purpose

Generate the full knowledge base from `staging/` and `wiki/queries/`.
Produces the glossary, one Markdown page per entity, and both entry points
(`wiki/index.yaml` for agents, `wiki/index.md` for Obsidian).

---

## Invocations

```
/kp-wiki build                   # full rebuild from all extractions
/kp-wiki update                  # rebuild only pages affected by new/changed extractions
/kp-wiki add-page <topic>        # create a manual page (generated: false)
```

---

## Internal pipeline (build)

1. **Read** all `staging/<source-id>.json` files.
2. **Read** `wiki/queries/` frontmatter (for feedback signals).
3. **Resolve entities** - merge aliases across extractions, deduplicate.
4. **Write** `wiki/glossary.md`.
5. **Write** one `wiki/<type>/<topic>.md` per resolved entity.
6. **Write** `wiki/index.md` (Obsidian entry point).
7. **Write** `wiki/index.yaml` (agent entry point).
8. **Report** any broken `[[wikilinks]]` and `index.yaml` file refs as warnings.

---

## Output

```
wiki/
├── index.yaml
├── index.md
├── glossary.md
├── concepts/<topic>.md
├── people/<topic>.md
├── organizations/<topic>.md
├── places/<topic>.md
├── products/<topic>.md
├── events/<topic>.md
└── other/<topic>.md
```

### `wiki/index.yaml` schema

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

gaps:                           # populated from wiki/queries/ low-confidence entries
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

Pages with `generated: false` (set by `/kp-wiki add-page` or manually) are never
overwritten by `/kp-wiki build`.

### `wiki/glossary.md` structure

Alphabetically sorted. Each entry:

```markdown
## Jane Smith

**Aliases**: J. Smith

Researcher and lead author of the 2025 report.

**Sources**: [[src-002]]
**Related**: [[Large Language Model]], [[OpenAI]]
```

---

## Feedback from `wiki/queries/`

Before writing, `/kp-wiki build` reads the frontmatter of all files in
`wiki/queries/`. It uses:

- `confidence: low` entries → populate `gaps` in `wiki/index.yaml`; these
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
- `wiki/index.yaml` generation and schema validation
- File-by-file incremental diffing for `update`
