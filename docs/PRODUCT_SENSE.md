# Product Sense

→ See [AGENTS.md](../AGENTS.md) for the full repository map.

---

## The problem

Most knowledge projects already have documentation. The problem is not that the
knowledge does not exist — it is that it exists in a form that neither humans
nor agents can use efficiently.

For humans: the material is scattered, unindexed, and too voluminous to read in full.

For agents: the material is unstructured prose. Agents can read it, but only when
it is in context. Loading everything is expensive and often impossible. Terminology
is ambiguous — the same concept appears under five names across five documents.
There is no entity index, no alias resolution, no way to answer "what do we know
about X" without scanning everything. One-off answers vanish when the conversation ends.

What is missing is a pipeline that transforms existing documentation into
**agentic documentation**: a file-based semantic layer that is permanently
queryable, cross-linked, and structured for non-linear agent access — not
just for humans reading linearly.

---

## The bet

Two principles together solve this.

**Progressive disclosure**: the pipeline produces useful artifacts at every stage,
so nothing has to be fully processed before anything is usable:

- After `ingestion`: you know what you have and where it came from.
- After `extract`: each source is summarized and its entities are named.
- After `kb build`: terms are defined, aliases resolved, cross-references built, and the knowledge is navigable and linkable — glossary and wiki pages are generated together in one step.
- After `query`: each question is saved with its answer and answer sources. On the next `/kb build`, the KB reorganizes around what was actually asked — compound knowledge accumulates.

**File-based semantic layer**: rather than a database or a vector store,
the structured knowledge lives as plain files — JSON extractions, a glossary,
Markdown wiki pages. This means it is git-versionable, diff-able, inspectable
by humans, and loadable by agents on demand without infrastructure.

Together they produce **good AX (Agent Experience)**: agents can navigate the
knowledge graph from a stable entry point, resolve terminology precisely,
attribute every fact to a source, and identify gaps rather than hallucinating.

A small set of composable, well-scoped commands automates this pipeline
incrementally. The user's job shifts from extraction to curation and questioning.

---

## Who this is for

**Primary**: researchers, analysts, and knowledge workers who regularly deal
with large volumes of documents and need to synthesize across them.

**Secondary**: engineering teams using AI assistants (Claude Code, Cursor,
Codex) who want to apply the same pipeline to internal documentation,
architecture decisions, or competitive research.

---

## Non-goals

- General-purpose RAG or chatbot infrastructure
- Replacing domain-specific tools (e.g., citation managers, spreadsheets)
- Real-time data pipelines or streaming sources

---

## Success criteria

A user with 50 PDFs they have never read can, within 30 minutes:

1. Run `init` and `ingestion add` to ingest all sources.
2. Run `extract --all` to produce structured extractions.
3. Run `kb build` to generate the glossary, entity pages, and navigable KB.
4. Answer three non-trivial cross-source questions using `query`.

The answers are grounded in source material, citable, and accurate enough
that the user trusts them as a starting point for deeper reading.

---

## Inspired by

- [ai-research-os-workshop](https://github.com/iusztinpaul/ai-research-os-workshop) — vocabulary and concept framing
- [Harness Engineering](https://openai.com/index/harness-engineering/) — documentation structure and agent-first operating model
