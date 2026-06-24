# Feature Backlog

Ideas and wanted features not yet scheduled. Add entries freely; move to an exec-plan when work begins.

---

## Extraction

- **Question-driven extraction**: use `kb/questions/` as input to `/extract` so that low-confidence or unanswered questions steer what the extractor focuses on. Questions with `confidence < threshold` could generate targeted extraction prompts rather than running the default full-document pass.

- **Rich content blocks in entity extraction**: the extractor reduces all entities to a one-liner `context` and scatters rules as disconnected `key_facts`. Meaningful chunks of source content -- rule procedures, worked examples, tables, lore passages -- are discarded. Add a `body` field to the entity schema so the extractor can write the full relevant content as markdown for any entity that warrants it. Also extend the extraction prompt to explicitly create entities for rule systems and mechanics (Combat, Saves, Healing, etc.), not just named vocabulary terms. See exec-plan: `docs/exec-plans/active/structured-content-in-kb.md`.

## KB

- **Question-driven KB page enrichment (write-back)**: when `/query` answers a question by going to source and the answer is richer than the current KB page (e.g. the page is a stub, or no page exists at all for the topic), flag the page as `enrichment_needed` in the question frontmatter. A new `/kb enrich` sub-command surfaces those gaps and suggests the exact re-extract commands. Distinct from question-driven extraction (which steers focus) -- this one propagates already-found rich content back into KB pages. See exec-plan: `docs/exec-plans/active/structured-content-in-kb.md`.

## Ingestion

- **Obsidian vault support**: when the source is detected as an Obsidian vault (presence of `.obsidian/` dir), prompt the user whether to import the full vault or filter to pages related to specific topics. Topic filter could match on tags, folder paths, or a seeded keyword list.
