---
name: kp-query
description: >
  Ask a question against the wiki and save the answer with full
  provenance to wiki/queries/. Searches wiki/index.yaml, entity pages, glossary,
  and staging in priority order. Records confidence and answer sources so
  each question improves the next /kp-wiki build. Use when the user runs /kp-query,
  asks a question about the project's sources or wiki, wants to find
  low-confidence gaps, or wants to explore past questions related to a topic.
  "kps" is the short name for this project (Knowledge Project Skills) - also
  activate when the user says "kps query".
metadata:
  version: "1.2"
  project: knowledge-project-skills
---

## Instructions

### When to activate

Activate when the user invokes `/kp-query`, asks a question about the project
sources, or wants to review past questions with `--gaps` or `--related`.

---

### Sub-commands

#### `"<question>"`

Answer a question grounded in the wiki.

**Search priority order:**

1. Read `wiki/index.yaml` - check if the topic maps to a known entity or appears
   in `search_hints`.
2. Read the matching `wiki/<type>/<topic>.md` page if found.
3. Read `wiki/glossary.md` for term definitions.
4. Scan `staging/<source-id>.json` - search `key_facts` and `summary`
   fields if no wiki page covers the topic.
5. Scan `wiki/queries/` frontmatter - check if a past question closely matches;
   surface the prior answer as context.

**Assign confidence:**

| Level | Condition |
|---|---|
| `high` | Answered from a wiki page or glossary with a clear `source_ref` |
| `medium` | Answered from staging directly; no wiki page exists yet |
| `low` | No strong match; answer is inferential or the wiki/staging are empty |

**Save to `wiki/queries/`:**

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
  - type: wiki_page | staging | source
    ref: <relative path>
related_questions: []
enrichment_needed: true | false
enrichment_target: <relative wiki path e.g. concepts/combat> | null
---

## Question

<question text>

## Answer

<answer>

## How this was answered

<one short paragraph: which files were consulted, why confidence is what it is>
```

**Enrichment (inline, automatic)**

When the answer comes from staging or source (not a wiki page), detect whether
a gap exists:

- **Gap condition A:** a wiki page for the topic exists but is thinner than the
  answer (heuristic: answer body is more than 2x the wiki page body length, or
  the answer contains structured content such as a table or numbered list that
  the wiki page lacks).
- **Gap condition B:** no wiki page exists for the topic at all.

If either condition is met, enrich immediately before finishing:

1. Identify the source(s) to re-stage:
   - If a wiki page exists: read its `sources:` frontmatter list.
   - If no wiki page: find which staging JSON files contain the entity by name.
2. Re-stage each source with `--force` (invoke the kp-staging skill).
3. Run `<kp-wiki-skill-dir>/scripts/wiki_build.py --mode build` to write the enriched
   `body` into the wiki page.
4. Re-read the newly built wiki page and use it to improve or confirm the answer.
5. Save the query file with `enrichment_needed: false` (gap resolved inline).

Tell the user in the answer that the wiki page was enriched as a side effect,
e.g. "I've also updated `wiki/concepts/combat.md` with the full rules."

If enrichment fails (staging error, no source found): fall back to answering
from what was found, save `enrichment_needed: true` and `enrichment_target` for
later resolution via `/kp-wiki enrich`.

If no gap is detected, save `enrichment_needed: false` as usual.

If `wiki/` does not exist: fall back to searching `staging/` directly.
Still write the query file (create `wiki/queries/` if needed).

---

#### `--gaps`

Read frontmatter of all files in `wiki/queries/` (frontmatter only, no body).
List questions where `confidence` is `low` or `medium`, sorted by date descending.

Output columns: `date`, `confidence`, `question`, `file`.

Also list questions where `enrichment_needed: true`, grouped separately under
an "Enrichment gaps" heading. For each, show: `date`, `question`,
`enrichment_target` (or "no page exists" when null).

Suggest running `/kp-staging --all --force` for topics with multiple low-confidence
entries, and `/kp-wiki build` after to close the loop. For enrichment gaps that were
not resolved inline (failed staging), suggest `/kp-wiki enrich` to retry them.

---

#### `--related "<topic>"`

Scan frontmatter of all files in `wiki/queries/` for files whose `question`
field or `answer_sources` reference the topic string (case-insensitive).

Return matching files sorted by date descending. For each match, print:
date, confidence, question text, and file path.

---

### Edge cases

- No staging and no wiki: answer from general knowledge only. Set
  `confidence: low`. State clearly in the answer that no project sources were found.
- Long answer that references many sources: list the top 3 most relevant
  `answer_sources`; do not list every file scanned.
- `--gaps` or `--related` with no `wiki/queries/` directory: print a message
  that no questions have been asked yet.
