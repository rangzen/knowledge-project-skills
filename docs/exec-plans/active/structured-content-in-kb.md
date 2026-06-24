# Plan: Rich Content in KB Pages

## Problem

KB pages for concept entities are thin stubs. The root cause is a pipeline hole that spans three layers:

1. **Extraction flattens everything to one-liners.** Every entity gets a `context` (single sentence). Key facts are individual one-liners. Meaningful content blocks from the source -- rule procedures, worked examples, tables, lore passages -- are discarded or scattered as disconnected `key_facts` with no entity to attach to.
2. **KB builder only uses `entity.context` as page body.** Pages are generated from the one-liner, nothing more.
3. **Entities are not created for rule systems.** Mechanics like "Combat" never become entities because the extraction prompt targets named vocabulary terms, not procedures. Their rules exist as free-floating `key_facts` with no KB page to land on.
4. **Query write-back is absent.** When `/query` goes to source and finds richer content than what the KB page holds, it stays in the question file and is never propagated back.

Concrete symptoms from the Cairn example:
- `kb/concepts/scars.md`: says "A 12-entry table..." but contains no rows. A user asking "what is scar 7?" falls back to the source PDF.
- `kb/concepts/combat.md`: does not exist. Four combat rules float as `key_facts` with no home.

## Goal

After this plan is complete:
- Entities have a `body` field in the extraction that carries the full meaningful content from the source: rules, procedures, tables (as markdown), examples, anything substantial.
- Rule systems and game mechanics are extracted as concept entities, not just scattered key_facts.
- The KB builder uses `body` as the page content when present.
- `/query` flags KB pages that are thinner than the answer it had to derive from source, so the next re-extraction pass knows where to focus.

---

## Phase 1 — Extraction: entity `body` field

**What to change**

Add an optional `body` field to the entity schema. It is a markdown string that carries any substantial content the extractor finds in the source for that entity. `context` stays as the one-liner (used for the glossary). `body` becomes the KB page content.

Updated entity structure:

```json
{
  "name": "Combat",
  "type": "concept",
  "aliases": ["Combat rules"],
  "context": "The turn-based combat resolution system in Cairn.",
  "body": "## Turn order\n\nCombat has no fixed initiative. Each round, players declare actions and the Warden adjudicates order by fiction.\n\n## Attacking\n\nAttackers roll their weapon damage die and subtract the target's Armor value. Unarmed attacks always deal d4.\n\n- **Multiple attackers:** when several attackers target the same foe, roll all damage dice and keep only the single highest result.\n- **Impaired attacks** (restricted position, distracted, etc.): roll d4 regardless of weapon.\n- **Enhanced attacks** (special advantage): roll d12.\n\n## Morale\n\nEnemies must pass a WIL save to avoid fleeing after their first casualty and again when they lose half their number.\n\n## Example\n\nThree players attack a Wood Troll. They roll d6, d8, and d6 and get 4, 7, and 2. Only 7 is dealt — the Troll has 1 Armor, so it takes 6 damage.",
  "source_ref": "sources/cairn/Cairn.pdf"
}
```

Rules for `body`:
- Write it when the entity represents a meaningful block of content: a mechanic, a procedure, a reference table, a lore section, a list of items with descriptions.
- Use markdown: headers for sub-sections, bullet lists for options, pipe tables for tabular data, blockquotes for examples.
- Prefer content the user would look up during play over incidental mentions.
- Skip `body` for shallow entities (a person's name, a product citation) where `context` is already complete.
- Tables that exist in the source should be reproduced as markdown tables inside `body`, not in a separate field.

Updated extraction rule in the prompt: "For each entity that represents a mechanic, procedure, system, or reference -- write a `body` field containing the full relevant content from the source in clean markdown. Include sub-rules, steps, tables, and examples if present. Omit `body` for shallow entities where the one-line `context` is sufficient."

**Entities to create that are currently missing**

The extraction prompt must also be updated to explicitly create entities for **rule systems and game mechanics**, not just named vocabulary terms. Examples from Cairn that should become entities but don't:
- `Combat` -- the full procedure
- `Saves` -- when and how to roll d20-under
- `Healing` -- rest and recovery rules
- `Inventory` -- slots, encumbrance, full inventory effect
- `Character Creation` -- the step-by-step procedure

Update the entity extraction rule: "Include entities for significant rule systems, mechanics, and procedures -- these are just as important as named terms. A rule system is significant if it has its own section heading in the source or is referenced repeatedly."

**Files to change**

- `skills/extract/SKILL.md`
  - Add `body` to the entity object in the extraction prompt template.
  - Add `body` to the Output schema table with description "Optional markdown string. Full content block for the entity. Omit for shallow entities."
  - Update the `entities` extraction rule to include the `body` guidance and the mechanic/procedure guidance above.
- `skills/extract/scripts/write_extraction.py`
  - Accept `body` in entity objects; pass through to output without modification.
  - Do not require it; existing extractions without `body` remain valid.

**Schema version**: keep `"1"`. `body` is optional and additive.

**Test fixture**

`tests/data/pdf/rules-quickstart.pdf` (generated by `tests/generate_fixtures.py`) is the canonical fixture for this plan. It contains:
- **Combat** (page 2): a multi-section procedure with sub-rules (Multiple Attackers, Impaired/Enhanced, Morale) and a worked example (three players vs. a Stone Golem).
- **Wounds** (page 3): a named d6 lookup table with 6 rows and surrounding rule text.
- **Shallow entities** (page 1): Aldric (person), Ironforge (product), The Depths (place) -- context-only, no body needed.

**Acceptance criteria**

- Extracting `rules-quickstart.pdf` produces a `Combat` entity with a `body` containing at minimum: the multiple-attacker rule, the impaired/enhanced rule, the morale rule, and the worked Stone Golem example.
- Extracting produces a `Wounds` entity with a `body` containing all 6 rows as a markdown table.
- Shallow entities (`Aldric`, `Ironforge`, `The Depths`) have no `body` field or an empty one.
- `write_extraction.py` does not reject entities without `body`.

---

## Phase 2 — KB builder: use `body` as page content

**What to change**

When `kb_build.py` generates an entity page, use `body` as the page content if present. Fall back to `context` when `body` is absent (current behavior, unchanged for shallow entities).

Entity page for `Combat` after this change:

```markdown
---
title: Combat
entity_type: concept
generated: true
sources:
  - cairn
last_built: 2026-06-24
---

# Combat

The turn-based combat resolution system in Cairn.

## Turn order

Combat has no fixed initiative. Each round, players declare actions and the Warden adjudicates order by fiction.

## Attacking

Attackers roll their weapon damage die and subtract the target's Armor value...

...
```

The one-liner (`context`) becomes the lead paragraph under the heading. The `body` content follows.

**Files to change**

- `skills/kb/scripts/kb_build.py`
  - In the entity dict built from extractions, store `body` alongside `context`.
  - In the page-writer: write `context` as the lead paragraph, then append `body` content if present.
  - If the same entity appears in multiple extractions with different `body` values, concatenate them under a source attribution header (e.g. `### From cairn`).
- `skills/kb/SKILL.md`
  - Document the `body` field in the entity page description.

**Acceptance criteria**

- After extracting `rules-quickstart.pdf` and running `/kb build`: `kb/concepts/combat.md` contains the multiple-attacker rule, impaired/enhanced rule, morale rule, and the Stone Golem example.
- `kb/concepts/wounds.md` contains the full 6-row Wounds table as markdown.
- Entities with no `body` (`Aldric`, `Ironforge`, `The Depths`) render exactly as before (context one-liner only).

---

## Phase 3 — Query write-back: flag thin pages for enrichment

**What to change**

**3a — `/query` flags enrichment gaps**

When `/query` answers by going to source (answer_source type `source`) and a KB page exists for the topic, compare answer richness to the KB page body. If the answer is substantially richer (heuristic: answer body > 2x KB page body length, or answer contains structured content the KB page lacks), set in the saved question frontmatter:

```yaml
enrichment_needed: true
enrichment_target: concepts/scars
```

When `/query` answers a question but no KB page exists at all for the entity (e.g. "combat" maps to no page), set:

```yaml
enrichment_needed: true
enrichment_target: null   # entity page missing entirely
```

- `skills/query/SKILL.md`: add `enrichment_needed` and `enrichment_target` to the question file format. Document the heuristic. This is advisory -- the user triggers enrichment manually.

**3b — `/kb enrich` sub-command**

New sub-command that surfaces the gaps:

1. Read all `kb/questions/` files where `enrichment_needed: true`.
2. For each, report: date, question, target page (or "no page exists"), source to re-extract.
3. Print the exact `/extract --force <source-id>` command(s) to run.
4. After the user re-extracts and runs `/kb build`, the enriched `body` lands in the page.
5. Clear `enrichment_needed` on question files whose target page now has a `body`.

- `skills/kb/SKILL.md`: add `enrich` sub-command spec.
- `skills/kb/scripts/kb_build.py`: add `--mode enrich`.

**Acceptance criteria**

- After extracting `rules-quickstart.pdf` with the current schema (no `body`) and asking "what is wound 4?": question file has `enrichment_needed: true`, `enrichment_target: concepts/wounds`.
- After asking "how does combat work?": question file has `enrichment_needed: true`, `enrichment_target: concepts/combat` (or `null` if no Combat page exists yet).
- `/kb enrich` lists both gaps and prints the suggested `--force` re-extract commands.
- After re-extracting with the Phase 1 schema and rebuilding, `/kb enrich` clears both flags.

---

## Execution order

| Step | Phase | Effort | Dependency |
|---|---|---|---|
| 1 | Phase 1 — add `body` to extraction schema + prompt | small | none |
| 2 | Phase 1 — write_extraction.py pass-through | small | step 1 |
| 3 | Phase 2 — kb_build.py uses `body` as page content | small | step 1 |
| 4 | Phase 3a — query flags `enrichment_needed` | small | none |
| 5 | Phase 3b — `/kb enrich` sub-command | medium | steps 3 + 4 |

---

## Decision log

| Date | Decision | Reason |
|---|---|---|
| 2026-06-24 | `body` on the entity, not a separate `tables[]` or `sections[]` field | Tables are one shape of meaningful content; a unified markdown field handles tables, prose rules, examples, and anything else without schema proliferation |
| 2026-06-24 | `context` stays as the one-liner; `body` is the additive content | Glossary needs a one-liner; KB page needs substance. Separating them avoids forcing a compromise |
| 2026-06-24 | `body` is markdown, not structured JSON | The KB is Obsidian markdown; freeform markdown is the natural format and avoids a renderer layer |
| 2026-06-24 | Schema version stays "1"; `body` is optional | Additive field; all existing extractions remain valid |
| 2026-06-24 | Enrichment loop is user-triggered, not automatic | Automatic re-extraction on every thin-page query would be too costly and noisy |
| 2026-06-24 | Extraction prompt must explicitly name mechanics/procedures as valid entity types | The extractor was creating vocabulary-term entities but skipping rule systems like Combat; explicit guidance is needed |
