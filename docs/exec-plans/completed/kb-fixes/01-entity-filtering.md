# 01 — Entity Filtering Before Page Generation

## Problem

The KB builder blindly promotes all extraction entities to pages, producing false-positive topics like `About`, `Access`, `Activating`, and document codes like `AD31971-EN`. These clutter the KB and generate broken wikilinks in bulk.

## Steps

1. Add a pre-generation filter step in `kb_build.py` before entities are promoted to pages.

2. Implement the following filters (in order):

   a. **Stoplist filter**: drop entities whose normalized name matches a list of known low-value tokens (section headers, common verbs, generic nouns). Maintain the stoplist in a config file (`kb/config/entity_stoplist.txt`) so it can be extended without code changes.

   b. **Document-code filter**: drop entities that match a document-code pattern (e.g. all-caps alphanumeric with hyphens and no spaces) unless they are explicitly typed as `document`.

   c. **Single-context filter**: optionally require an entity to appear in more than one source context before promotion to a page. Make this threshold configurable (default: 1, meaning no filter; set to 2 to require cross-source presence).

3. Log filtered entities at build time:
   ```
   Filtered 42 low-value entities before page generation.
   ```

4. Add acceptance tests:
   - Entity `About` → filtered by stoplist.
   - Entity `AD31971-EN` (no type) → filtered by document-code rule.
   - Entity `MyCenter` appearing in 2 sources with threshold=2 → promoted.

## Acceptance criteria

- Common section headers and generic words do not become KB pages.
- Document codes without an explicit `document` type are excluded.
- Filter counts are reported at build time.
- The stoplist is configurable without code changes.
