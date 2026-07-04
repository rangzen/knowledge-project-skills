# Architecture

→ See [AGENTS.md](AGENTS.md) for the full repository map.
→ See [docs/references/agentskills-io-specifications.md](docs/references/agentskills-io-specifications.md) for the Agent Skills format spec.

---

## Skill format

This repository follows the [Agent Skills](https://agentskills.io) open standard.
Each skill is a **folder** containing a `SKILL.md` file with metadata and
instructions. Skills are loaded by compatible agents (Claude Code, Cursor, Codex,
Gemini CLI, and others) from their configured skills directory.

```
<skill-name>/
├── SKILL.md          # Required - name, description, instructions
├── scripts/          # Optional - Python scripts for reproducible operations
├── references/       # Optional - documentation, llms.txt files
└── assets/           # Optional - templates, static resources
```

### SKILL.md structure

```markdown
---
name: <skill-name>
description: <one or two sentences - used for discovery>
---

## Instructions
...
```

The `description` is the discovery key: agents load only `name` + `description`
at startup, then read the full file when a task matches. Keep descriptions precise
so activation fires on the right tasks - not too broad, not too narrow.

---

## Repository layout

```
knowledge-project-skills/
├── skills/                   ← skill folders (npx skills, Claude Code, Cursor, etc.)
│   ├── kp-init/                 ← /kp-init skill
│   │   └── SKILL.md
│   ├── kp-source/            ← /kp-source skill
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── kp-staging/              ← /kp-staging skill
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── kp-wiki/                   ← /kp-wiki skill
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── kp-query/                ← /kp-query skill
│       └── SKILL.md
├── AGENTS.md
├── ARCHITECTURE.md
├── README.md
└── docs/
```

Skills that include a `scripts/` directory use Python for operations where
reproducibility matters (parsing source files, writing structured output).
Not every skill needs scripts - `init` and `query` may be fully instruction-driven.

---

## The knowledge pipeline

The five skills collectively implement a **knowledge pipeline**: a staged
transformation from raw sources to a navigable, agent-ready knowledge base.

```
sources/  →  ingestion  →  extraction  →  kb build  →  query
(raw)         (tracked)    (structured)    (semantic     (compound
                                            layer)        knowledge)
```

Each stage produces artifacts consumed by the next. The pipeline is designed
for incremental operation - any stage can run independently on partial data.

### Stage artifacts

```
sources/
  └─ <source-id>/
        ├── <file>           ← ingestion writes
        └── .meta.json       ← ingestion writes (provenance: origin, hash, date)

staging/
  └─ <source-id>.json        ← extract reads sources/, writes structured JSON
                               fields: entities, summary, key_facts, dates,
                               schema (structured sources), images (PDFs), source_ref

wiki/
  ├── index.yaml             ← kp-wiki reads staging/ + queries/, writes
  ├── index.md               ← kp-wiki reads staging/ + queries/, writes
  ├── glossary.md            ← kp-wiki reads staging/, writes
  ├── <type>/<topic>.md      ← kp-wiki reads staging/, writes one page per entity
  └── queries/
        └── YYYY-MM-DD-<slug>.md  ← kp-query writes; kp-wiki reads back on next build
```

### Compound knowledge loop

`wiki/queries/` closes a feedback loop: each answered question - with its
confidence level and answer sources - is read by the next `/kp-wiki build` to
prioritize frequently asked topics and flag extraction gaps.

```
kp-query → wiki/queries/ → kp-wiki build → better wiki → better answers → kp-query → …
```

---

## Semantic layer

The pipeline's output forms a **file-based semantic layer**: a structured,
navigable representation of the domain knowledge stored as plain files —
git-versionable, agent-readable, no database required.

```
Semantic layer
├── staging/      ← entity index, per source (JSON)
└── wiki/               ← resolved, cross-linked, agent-ready
    ├── index.yaml    ← agent entry point (typed links, metadata, search hints)
    ├── index.md      ← human / Obsidian entry point
    ├── glossary.md   ← resolved terminology, cross-source
    ├── questions/    ← compound query knowledge
    └── <topic>.md    ← one page per entity or concept
```

---

## Layering rules

1. **No reverse dependencies.** `kb` never writes to `staging/`.
2. **Extractions are immutable after generation.** Re-running `extract` replaces, never patches.
3. **Glossary is derived, not authoritative.** Source of truth is the extraction, not `wiki/glossary.md`.
4. **The KB is a view.** Rebuild from scratch at any time. Pages with `manual: true` frontmatter are preserved.
5. **`wiki/index.yaml` is the agent contract.** Schema is versioned; breaking changes require a version bump in `.knowledge-project`.

---

## Compatibility

Concept mapping to [ai-research-os-workshop](https://github.com/iusztinpaul/ai-research-os-workshop):

| This project | ai-research-os-workshop |
|---|---|
| `sources/` | raw data / documents layer |
| `staging/` | processed / structured layer |
| `wiki/glossary.md` | ontology / vocabulary |
| `wiki/` | knowledge base |
| `wiki/queries/` | retrieval + feedback loop |
