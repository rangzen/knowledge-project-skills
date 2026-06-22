# Spec: query

**Status**: draft
**Command**: `/query`
**SKILL.md description**: Ask a question against the knowledge base and save the answer with full provenance to kb/questions/. Use when the user runs /query, asks a question about the project's sources, wants to find low-confidence answers, or wants to explore past questions related to a topic.

---

## Purpose

Answer questions grounded in the knowledge base and persist each answer — with
its sources and confidence — as a Markdown file in `kb/questions/`. These files
feed back into the next `/kb build`, making the knowledge base progressively
better at answering related questions.

---

## Invocations

```
/query "What are the main findings in the 2025 report?"
/query --gaps                       # list low-confidence questions from kb/questions/
/query --related "fine-tuning"      # show past questions related to a topic
```

---

## Answer strategy

Answer questions by searching in priority order:

1. `kb/index.yaml` — check if the topic maps to a known entity page.
2. `kb/<type>/<topic>.md` — read the entity page if found.
3. `kb/glossary.md` — check for term definitions.
4. `extractions/<source-id>.json` — search `key_facts` and `summary` fields
   directly if the KB does not cover the topic.
5. `kb/questions/` — check if a past question closely matches; surface the
   prior answer as context.

Assign a confidence level:
- `high` — answered from a KB entity page or glossary with a clear `source_ref`.
- `medium` — answered from extractions directly; no KB page exists yet.
- `low` — no strong match found; answer is inferential or partial.

---

## Output

One Markdown file per question:

```
kb/questions/YYYY-MM-DD-<slug>.md
```

Slug: lowercase, hyphens, max 60 chars, derived from the question text.

### Question file format

```markdown
---
date: 2026-06-21
question: "What are the main findings in the 2025 report?"
confidence: high
answer_sources:
  - type: kb_page
    ref: kb/concepts/findings-2025.md
  - type: extraction
    ref: extractions/src-001.json
  - type: source
    ref: sources/src-001/report-2025.pdf
related_questions:
  - 2026-06-20-what-changed-since-2024.md
---

## Question

What are the main findings in the 2025 report?

## Answer

...

## How this was answered

The answer was composed from the KB page [[findings-2025]] (high confidence)
and cross-checked against the raw extraction for `src-001`.
```

---

## `--gaps`

Read frontmatter of all files in `kb/questions/`. List questions where
`confidence: low` or `confidence: medium`, grouped by topic. Output is a
concise table: question slug, confidence, date, related entity (if any).

This output is the recommended input to the next `/extract --all --force`
run — gaps indicate where more extraction work is needed.

---

## `--related <topic>`

Scan frontmatter of all files in `kb/questions/` for questions whose
`answer_sources` reference the same entity or whose question text contains
the topic string. Return matching question files sorted by date descending.

Reads frontmatter only — no full-text load — so it stays fast at scale.

---

## Behavior

- If `kb/` does not exist: fall back to querying `extractions/` directly.
  Still write the question file to `kb/questions/` (create directory if needed).
- If no extractions exist: answer from agent knowledge only; set
  `confidence: low`; note the absence of sources in the answer.
- Slug collisions (same question asked twice on the same day): append `-2`,
  `-3`, etc.

---

## Scripts

Query is primarily instruction-driven. A lightweight script may assist with:
- Frontmatter-only scanning of `kb/questions/` for `--gaps` and `--related`
- Slug generation from question text
