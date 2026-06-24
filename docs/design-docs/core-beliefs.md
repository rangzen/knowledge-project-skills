# Core Beliefs — Agent-First Operating Principles

These beliefs define how this repository approaches knowledge work.
They are constraints, not guidelines — when a design decision conflicts with
a belief listed here, the belief wins unless explicitly revisited.

---

## 1. Knowledge is the artifact, not code

Code in a knowledge project is infrastructure. The deliverable is structured,
queryable, cross-linked knowledge. Optimizing for code cleanliness at the expense
of knowledge quality is the wrong trade.

**Implication**: Skills are judged by the quality of their output artifacts
(`extractions/`, `kb/`), not by code elegance.

---

## 2. Provenance is non-negotiable

Every extracted fact must be traceable to its source. An unsourced claim is
an unverified claim. The pipeline must maintain `source_ref` at every stage.

**Implication**: Skills that drop provenance metadata (even for convenience)
are not acceptable. See [ARCHITECTURE.md](../../ARCHITECTURE.md) for the
`source_ref` field contract.

---

## 3. Extraction is progressive, not one-shot

A first pass produces rough structure. Subsequent passes refine, add relations,
and resolve conflicts. The pipeline is designed for iteration, not for single runs.

**Implication**: Re-running `extract` replaces the previous output rather than
patching it. Version history is preserved by git, not by the skill itself.

---

## 4. Agents start from stable entry points

Context injection is expensive. Agents are given AGENTS.md as a minimal, stable
map and directed to specific docs on demand — not a full knowledge dump.

**Implication**: AGENTS.md must stay under ~100 lines. Detail belongs in the doc
it describes, not in the map.

---

## 5. Questions are compound knowledge

Every question asked — and how it was answered — is saved to `kb/questions/`
as a first-class KB artifact. The record includes: the date, the question,
the answer, which KB pages / extractions / raw sources were consulted, and
the confidence level.

On the next `/kb build`, these files are read as an additional input layer:
- Frequently asked topics become first-class KB pages.
- Low-confidence answers flag extraction gaps for the next `/extract` pass.
- The answer-source trail informs how entities and relationships are weighted.

This creates a **compound knowledge loop**: each question makes future answers
to related questions easier and better, without re-reading the original sources.

**Implication**: `kb/questions/` is not a log to be archived or rotated. It is
a living part of the knowledge base, versioned alongside everything else in `kb/`.
Its value grows over time — discarding it discards accumulated query intelligence.

---

## 6. The KB is a view, not a source of truth

`kb/` is generated from extractions and the glossary. It can be rebuilt at
any time. Direct edits to `kb/` files are transient unless explicitly pinned
with `manual: true` in frontmatter.

**Implication**: Do not store original knowledge in `kb/`. Store it in
`sources/` and let the pipeline derive the rest. The one exception is
manually pinned pages, which are preserved across rebuilds.

---

## 7. Stale documentation is worse than no documentation

A doc that describes behavior that no longer exists misleads agents and humans
alike. Stale docs create false confidence. Maintenance of the knowledge base is
a first-class obligation.

**Implication**: CI validates cross-links and flags design docs whose described
behavior cannot be found in the implementation. See
[design-docs/index.md](index.md) for verification status tracking.

---

## 8. Progressive disclosure over front-loading

Agents and humans should be able to start from a small, stable entry point and
discover depth on demand. Overwhelming an agent with too much context up front
reduces precision.

**Implication**: Every index (AGENTS.md, design-docs/index.md,
product-specs/index.md) is a navigation aid, not a summary. Content lives in
the doc it belongs to.

---

## 9. Documentation should be written for agents, not just humans

Documentation that is readable by humans is not necessarily usable by agents.
Prose is ambiguous. Long-form text cannot be queried by entity or relationship.
Terminology that is obvious in context to a human ("the model", "the table")
is unresolvable for an agent without a glossary.

The pipeline's output — extractions and `kb/` (glossary + entity pages + indexes) — is
**agentic documentation**: structured for non-linear access, typed at the entity level,
and explicit about relationships and provenance. AX (Agent Experience) is a first-class design goal.

**Implication**: Extraction schema fields, glossary structure, and KB page frontmatter
are all designed with agent consumption as the primary use case. Human readability
is a constraint, not the target.

---

## 10. Three tiers of source handling — no hard failures

Sources fall into three tiers based on what is already known about them:

1. **Dedicated scripts**: PDF, DOCX, Excel, CSV, JSON. Scripts exist that
   extract content and structural metadata (page count, column names, row count,
   etc.) in a reproducible way. Always use them.
2. **Direct read**: plain-text formats (Markdown, plain text, Mermaid, and
   similar). Already readable as-is; no script needed.
3. **Ad-hoc**: any other format. Attempt a direct read first. If the content is
   not usable, write a small inline script to extract what is accessible and
   note what could not be extracted. Never refuse on the grounds that a format
   has no dedicated script.

**Implication**: The pipeline never has a hard "unsupported format" failure.
Every source gets a best-effort extraction attempt. Dedicated scripts are the
preferred path when available; ad-hoc handling is the fallback, not a dead end.

---

## 11. The file system is the semantic layer

A vector database, a graph database, or a search index all require infrastructure
and diverge from the source of truth over time. Plain files are always in sync,
git-versionable, diff-able, and accessible to any tool.

The three-tier file layout — `extractions/` (per-source entities),
`kb/glossary.md` (cross-source synthesis), `kb/*.md` + `kb/index.yaml`
(navigable graph with a typed agent entry point) — is the semantic layer.
No additional infrastructure is needed for an agent to traverse the knowledge graph.

**Implication**: Skills must not require a running service to function. The output
of every skill must be readable as a plain file. Search and traversal are
implemented over the file structure, not over an external index.
