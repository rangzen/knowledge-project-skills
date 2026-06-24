---
name: query
description: >
  Ask a question against the knowledge base and save the answer with full
  provenance to kb/questions/. Searches kb/index.yaml, entity pages, glossary,
  and extractions in priority order. Records confidence and answer sources so
  each question improves the next /kb build. Use when the user runs /query,
  asks a question about the project's sources or knowledge base, wants to find
  low-confidence gaps, or wants to explore past questions related to a topic.
  "kps" is the short name for this project (Knowledge Project Skills) — also
  activate when the user says "kps query".
metadata:
  version: "1.1"
  project: knowledge-project-skills
---

## Instructions

### When to activate

Activate when the user invokes `/query`, asks a question about the project
sources, or wants to review past questions with `--gaps` or `--related`.

---

### Sub-commands

#### `"<question>"`

Answer a question grounded in the knowledge base.

**Search priority order:**

1. Read `kb/index.yaml` — check if the topic maps to a known entity or appears
   in `search_hints`.
2. Read the matching `kb/<type>/<topic>.md` page if found.
3. Read `kb/glossary.md` for term definitions.
4. Scan `extractions/<source-id>.json` — search `key_facts` and `summary`
   fields if no KB page covers the topic.
5. Scan `kb/questions/` frontmatter — check if a past question closely matches;
   surface the prior answer as context.

**Assign confidence:**

| Level | Condition |
|---|---|
| `high` | Answered from a KB page or glossary with a clear `source_ref` |
| `medium` | Answered from extractions directly; no KB page exists yet |
| `low` | No strong match; answer is inferential or the KB/extractions are empty |

**Save to `kb/questions/`:**

Filename: `YYYY-MM-DD-<slug>.md`
Slug: lowercase, hyphens, max 60 chars, derived from the question text.
Slug collision same day: append `-2`, `-3`, etc.

File format:

```markdown
---
date: <ISO date>
question: "<question text>"
confidence: high | medium | low
answer_sources:
  - type: kb_page | extraction | source
    ref: <relative path>
related_questions: []
enrichment_needed: true | false
enrichment_target: <relative KB path e.g. concepts/combat> | null
---

## Question

<question text>

## Answer

<answer>

## How this was answered

<one short paragraph: which files were consulted, why confidence is what it is>
```

**Enrichment (inline, automatic)**

When the answer comes from extraction or source (not a KB page), detect whether
a gap exists:

- **Gap condition A:** a KB page for the topic exists but is thinner than the
  answer (heuristic: answer body is more than 2x the KB page body length, or
  the answer contains structured content such as a table or numbered list that
  the KB page lacks).
- **Gap condition B:** no KB page exists for the topic at all.

If either condition is met, enrich immediately before finishing:

1. Identify the source(s) to re-extract:
   - If a KB page exists: read its `sources:` frontmatter list.
   - If no KB page: find which extraction JSON files contain the entity by name.
2. Re-extract each source with `--force` (invoke the extract skill).
3. Run `<kb-skill-dir>/scripts/kb_build.py --mode build` to write the enriched
   `body` into the KB page.
4. Re-read the newly built KB page and use it to improve or confirm the answer.
5. Save the question file with `enrichment_needed: false` (gap resolved inline).

Tell the user in the answer that the KB page was enriched as a side effect,
e.g. "I've also updated `kb/concepts/combat.md` with the full rules."

If enrichment fails (extraction error, no source found): fall back to answering
from what was found, save `enrichment_needed: true` and `enrichment_target` for
later resolution via `/kb enrich`.

If no gap is detected, save `enrichment_needed: false` as usual.

If `kb/` does not exist: fall back to searching `extractions/` directly.
Still write the question file (create `kb/questions/` if needed).

---

#### `--gaps`

Read frontmatter of all files in `kb/questions/` (frontmatter only, no body).
List questions where `confidence` is `low` or `medium`, sorted by date descending.

Output columns: `date`, `confidence`, `question`, `file`.

Also list questions where `enrichment_needed: true`, grouped separately under
an "Enrichment gaps" heading. For each, show: `date`, `question`,
`enrichment_target` (or "no page exists" when null).

Suggest running `/extract --all --force` for topics with multiple low-confidence
entries, and `/kb build` after to close the loop. For enrichment gaps that were
not resolved inline (failed extractions), suggest `/kb enrich` to retry them.

---

#### `--related "<topic>"`

Scan frontmatter of all files in `kb/questions/` for files whose `question`
field or `answer_sources` reference the topic string (case-insensitive).

Return matching files sorted by date descending. For each match, print:
date, confidence, question text, and file path.

---

### Edge cases

- No extractions and no KB: answer from general knowledge only. Set
  `confidence: low`. State clearly in the answer that no project sources were found.
- Long answer that references many sources: list the top 3 most relevant
  `answer_sources`; do not list every file scanned.
- `--gaps` or `--related` with no `kb/questions/` directory: print a message
  that no questions have been asked yet.
