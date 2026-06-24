# AGENTS.md — Knowledge Project Skills

This file is injected into agent context. It is a **map**, not content.
Read it first, then follow pointers to the relevant source of truth.

---

## What this repository is

A collection of reusable agent skills for **knowledge projects** — projects where
the primary artifact is structured knowledge extracted from sources, not code.
Skills target Claude Code, Cursor, Codex, and compatible assistants.

→ Full description: [README.md](README.md)
→ Product vision: [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md)

---

## Commands (skills)

| Command | Purpose | Spec |
|---|---|---|
| `init` | Scaffold a new knowledge project | [product-specs/init.md](docs/product-specs/init.md) |
| `ingestion` | Add sources, track provenance, check updates | [product-specs/ingestion.md](docs/product-specs/ingestion.md) |
| `extract` | Run LLM/rule-based extractors over sources | [product-specs/extract.md](docs/product-specs/extract.md) |
| `query` | Ask questions, log answers, identify gaps | [product-specs/query.md](docs/product-specs/query.md) |
| `kb` | Build / update the knowledge base (`kb/`) — includes glossary generation | [product-specs/kb.md](docs/product-specs/kb.md) |

---

## Architecture

→ [ARCHITECTURE.md](ARCHITECTURE.md) — domain map, package layering, data flow

---

## Design

→ [docs/DESIGN.md](docs/DESIGN.md) — design principles and key decisions
→ [docs/design-docs/index.md](docs/design-docs/index.md) — catalogue with verification status
→ [docs/design-docs/core-beliefs.md](docs/design-docs/core-beliefs.md) — agent-first operating principles

---

## Plans

→ [docs/PLANS.md](docs/PLANS.md) — how plans work, index of active/completed
→ [docs/exec-plans/active/](docs/exec-plans/active/) — in-progress work (decision logs included)
→ [docs/exec-plans/completed/](docs/exec-plans/completed/) — finished plans kept for history
→ [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md) — known debt

---

## Quality, reliability, security

→ [docs/QUALITY_SCORE.md](docs/QUALITY_SCORE.md) — grades per domain, gap tracking
→ [docs/RELIABILITY.md](docs/RELIABILITY.md) — failure modes, graceful degradation
→ [docs/SECURITY.md](docs/SECURITY.md) — threat model, sensitive data handling

---

## Product specs

→ [docs/product-specs/index.md](docs/product-specs/index.md) — all specs indexed

---

## References

→ [docs/references/agentskills-io.md](docs/references/agentskills-io.md) — Agent Skills format spec (skill folder structure, SKILL.md, installation per agent)
→ [docs/references/](docs/references/) — all external reference material

---

## Skill format

Each skill is a folder with a `SKILL.md` file following the [Agent Skills](https://agentskills.io) open standard.
Some skills include a `scripts/` directory with Python scripts for reproducible operations.
When scripts exist, use them rather than generating equivalent code inline.

→ [ARCHITECTURE.md](ARCHITECTURE.md) — skill layout and knowledge pipeline
→ [docs/references/agentskills-io.md](docs/references/agentskills-io.md) — format spec and installation per agent

---

## Rules for agents

1. **AGENTS.md is a map.** Never inline detail here — link to the doc that owns it.
2. **Follow links before asking.** If a pointer exists, read the target first.
3. **Use skill scripts when present.** If a skill has a `scripts/` directory, use those scripts rather than generating equivalent code ad hoc.
4. **Plans are first-class.** Complex work gets a file in `docs/exec-plans/active/`.
5. **No orphan docs.** Every doc must appear in an index or be linked from here.
6. **Verification status matters.** Check `docs/design-docs/index.md` before trusting a design doc.
7. **Cross-link liberally.** Use relative Markdown links. `[[wikilinks]]` in `kb/` output only.
8. **Bump the minor version on every skill change.** When modifying a `SKILL.md`, increment the `metadata.version` minor number (e.g. `1.2` → `1.3`). After `1.9` the next version is `1.10`, not `2.0`.
9. **Commit message format.** Subject line: `topic_1: topic_2: short description` — all lowercase, no period. Then a blank line, then one explanation sentence per line, each starting with a capital letter and ending with a period. Example:
   ```
   extract: scripts: add two-stage extraction pipeline

   Adds preprocess_pdf.py and extract_llm.py to replace ad-hoc agent extraction.
   extract_llm.py validates LLM output against the schema before writing.
   ```
