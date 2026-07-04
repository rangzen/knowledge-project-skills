# KB Schema Reference

Full schema for `kb/index.yaml` and entity page frontmatter.

## `kb/index.yaml` schema

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

### Field definitions

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Must be `"1"` |
| `last_built` | ISO datetime string | When the KB was last built |
| `source_count` | int | Number of source extractions consumed |
| `entity_count` | int | Total resolved entities across all types |
| `glossary` | string | Relative path to glossary file |
| `pages` | object | Entity pages grouped by type |
| `pages.<type>[]` | list | Entries for concepts, people, organizations, events, topics |
| `pages.<type>[].title` | string | Canonical entity name |
| `pages.<type>[].file` | string | Relative path to the entity page |
| `pages.<type>[].aliases` | list of strings | Alternative names; omit if empty |
| `pages.<type>[].sources` | list of strings | Source IDs this entity appears in |
| `gaps` | list | Topics with low-confidence question entries |
| `gaps[].topic` | string | Topic keyword or phrase |
| `gaps[].question_count` | int | Number of low-confidence questions on this topic |
| `gaps[].max_confidence` | string | Highest confidence seen (`low` or `medium`) |

## Entity page frontmatter

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

| Field | Description |
|---|---|
| `title` | Canonical display name |
| `entity_type` | One of: `concept`, `person`, `organization`, `event`, `topic` |
| `generated` | `true` if built by `/kb`; set to `false` to protect from overwrite |
| `sources` | Source IDs this entity was extracted from |
| `last_built` | Date this page was last generated (ISO date) |

## `kb/glossary.md` entry format

```markdown
## Jane Smith

**Aliases**: J. Smith

Researcher and lead author of the 2025 report.

**Sources**: [[src-002]]
**Related**: [[Large Language Model]], [[OpenAI]]
```
