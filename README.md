# Knowledge Project Skills

A collection of reusable AI agent skills for **knowledge projects** — projects where
you already have documentation and want to prepare and extract it into structured,
queryable form so it is easier to use, search, and reason over.

Designed to work with Claude Code, Cursor, Codex, and similar AI coding assistants.

Some skills include Python scripts for operations that must be reproducible across
assistants and runs — parsing source files, running extractors, writing structured
output. When a skill ships scripts, they live in its `scripts/` directory and are
Python. Not every skill needs scripts; agent reasoning alone is sufficient for
operations that are naturally conversational.

[AI Research OS](https://github.com/iusztinpaul/ai-research-os-workshop) uses very
similar concepts, so names are intentionally chosen to be compatible with that
project's vocabulary. It predates this project, and several conventions here
(the skills scripts structure, for example) are borrowed from it.

---

## What is a knowledge project?

A knowledge project starts with existing documentation — PDFs, database exports,
internal wikis, research papers, transcripts — and treats it as raw material.
The goal is to **progressively extract, organize, and surface** the knowledge
inside that material so agents and humans can use it without reading everything.

The primary target is not code generation.
It is structured knowledge: entities, facts, relationships, timelines, summaries,
and a navigable wiki built from what was already written.

Examples:
- A product team with scattered specs and ADRs who wants a queryable knowledge base
- Competitive intelligence from earnings calls, filings, and analyst reports
- Research synthesis across hundreds of papers
- Domain glossary construction from technical documentation

---

## Agentic documentation enables progressive disclosure

The goal is **agentic documentation**: a file-based semantic layer structured
for agent consumption so that agents can navigate knowledge progressively —
starting from a small, stable entry point and going deeper on demand, without
loading the full corpus into context.

Traditional documentation is written for humans reading linearly. Agents work
differently: they query non-linearly, compose answers from fragments across
many sources, and need unambiguous terminology to avoid hallucination. Prose
that works for humans is verbose, context-dependent, and unsearchable at the
entity level.

The pipeline builds a four-tier semantic layer from your existing documentation:

| Tier | Files | What it gives agents |
|---|---|---|
| **Entity index** | `extractions/<id>.json` | Named entities with type, source, and context — per source |
| **Resolved glossary** | `kb/glossary.md` | Canonical terms, aliases, definitions, cross-references — across all sources |
| **Navigable KB** | `kb/*.md` with `[[wikilinks]]` | Relationship graph between concepts, readable in Obsidian or VS Code |
| **Agent index** | `kb/index.yaml` | Typed, structured entry point — no Markdown parsing required |

This structure makes progressive disclosure possible:

- `init` gives you the scaffold immediately.
- `ingestion` adds one source at a time.
- `extract` produces useful output per source — no need to wait for the full corpus.
- `kb build` improves incrementally with each new extraction — glossary and pages regenerate together.
- `query` works at any stage; each question is saved and feeds the next build.

An agent always starts from `kb/index.yaml` — a typed, stable map — and follows
links only as deep as the question requires. The semantic layer is what makes
that navigation precise instead of speculative.

### AX (Agent Experience) properties

- **Stable, typed entry point** — `kb/index.yaml` requires no Markdown parsing; agents read structure, not prose.
- **Alias resolution** — the glossary normalizes synonyms so agents do not treat "ML model", "model", and "trained model" as three different things.
- **Source attribution** — every fact carries `source_ref`, so agents cite and verify rather than assert.
- **Gap visibility** — each question records confidence and answer sources, giving `/kb build` a signal for where the layer is thin.

---

## Project layout (created by `init`)

```
project-root/
├── sources/              # Raw inputs: PDFs, URLs, database dumps, CSVs, etc.
│   └── <source-id>/      # One subdirectory per source
├── extractions/          # Structured output, one JSON per source
│   └── <source-id>.json  # Entities, summary, dates, key facts, schema, etc.
├── kb/                   # Knowledge base — generated and maintained by skills
│   ├── index.yaml        # Agent entry point: typed links, KB metadata, search hints
│   ├── index.md          # Human / Obsidian entry point: navigable starting page
│   ├── glossary.md       # Resolved terminology, aliases, cross-references
│   ├── questions/        # Compound query knowledge (feeds back into /kb build)
│   │   └── YYYY-MM-DD-<slug>.md  # One file per question: answer + how it was generated
│   └── <topic>.md        # One page per entity or concept (wikilinks throughout)
└── .knowledge-project    # Project config and schema version
```

---

## Skills / Commands

### `init`
Scaffold a new knowledge project in the current directory.

Creates the directory structure above, writes `.knowledge-project` with project metadata, and generates stub files so the pipeline has a known shape from the start.

```
/init
```

---

### `ingestion`
Manage sources: add new ones, check for updates, track provenance.

Operations:
- Add a PDF, URL, database connection, or CSV as a new source
- Check whether a previously seen source has changed
- Record ingestion metadata (ingested-at, hash, origin URL, page count, etc.)
- List all sources and their ingestion status

```
/ingestion add <path-or-url>
/ingestion status
/ingestion check-updates
```

---

### `extract`
Run LLM-based or rule-based extractors over ingested sources and write structured output to `extractions/`.

Each extraction produces a JSON file containing:
- `entities` — people, organizations, places, products, concepts
- `summary` — short and long-form summaries
- `key_facts` — discrete, citable claims
- `dates` — timeline events with ISO dates
- `schema` (for structured sources) — table names, column types, relationships
- `images` (for PDFs) — extracted figures with captions
- `source_ref` — back-pointer to the originating source

```
/extract <source-id>
/extract --all
/extract --model claude-opus-4-8
```

---

### `query`
Ask a question against the knowledge base. The question, answer, and a record of
how the answer was generated (which KB pages, extractions, or raw sources were
used, and with what confidence) are saved to `kb/questions/` as a dated Markdown file.

Each question file becomes part of the KB itself. On the next `/kb build` run,
the questions directory is read as an additional input: frequently asked topics
become first-class KB pages, low-confidence answers flag gaps for the next
`/extract` pass, and the answer-source trail informs how entities are linked.
This is **compound knowledge** — the KB gets better at answering related questions
over time without re-reading every source.

```
/query "What are the main claims about X?"
/query --gaps              # List low-confidence questions from kb/questions/
/query --related "X"       # Show past questions related to a topic
```

---

### `kb`
Build or update the knowledge base under `kb/` from extracted content.

Internally runs the full synthesis pipeline: resolves entity aliases, generates `kb/glossary.md`, writes one Markdown page per entity, and produces both entry points (`kb/index.md` for Obsidian, `kb/index.yaml` for agents). Also reads `kb/questions/` — frequently asked topics become first-class pages, low-confidence answers trigger extraction gap warnings.

```
/kb build
/kb update
/kb add-page <topic>
```

---

## Compatibility

Concept names align with [ai-research-os-workshop](https://github.com/iusztinpaul/ai-research-os-workshop):

| This project | ai-research-os-workshop |
|---|---|
| `sources/` | raw data / documents layer |
| `extractions/` | processed / structured layer |
| `kb/glossary.md` | ontology / vocabulary |
| `kb/` | knowledge base |
| `kb/questions/` | retrieval + feedback loop |

---

## Installation

Skills follow the [Agent Skills](https://agentskills.io) open standard — each
skill is a folder with a `SKILL.md` file, compatible with Claude Code, Cursor,
Codex, Gemini CLI, and others.

### Via skills.sh (recommended)

Install directly using the [skills.sh](https://skills.sh) CLI:

```bash
npx skills add https://github.com/rangzen/knowledge-project-skills
```

To update later:

```bash
npx skills update
```

### Manual install

Clone the repo and copy the skill folders into your agent's skills directory:

```bash
git clone https://github.com/<org>/knowledge-project-skills

# Claude Code (global):
cp -r knowledge-project-skills/skills/* ~/.claude/skills/

# Claude Code (project-local):
cp -r knowledge-project-skills/skills/* .claude/skills/

# Cross-agent (.agents/skills/ convention):
cp -r knowledge-project-skills/skills/* .agents/skills/

# Other agents: see docs/references/agentskills-io.md for per-agent paths
```

Skills that include a `scripts/` directory require Python 3.11+. Dependencies
are listed in each skill's `scripts/requirements.txt`.

---

## Status

Early development. Contributions and issue reports welcome.
