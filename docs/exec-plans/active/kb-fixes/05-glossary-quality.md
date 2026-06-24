# 05 — Glossary Quality

## Problem

Glossary entries are built directly from raw `entity["context"]`, which often yields table-of-contents lines, fragments, version strings, or headings with no definition. The glossary looks complete but is not useful.

## Steps

1. Add a glossary-entry quality check in `kb_build.py`:
   - Prefer `entity["summary"]` over `entity["context"]` when a summary is present and longer than the context.
   - Prefer fact sentences from `key_facts` when context is a heading or under 30 characters.
   - If neither source yields a usable definition (under 30 characters after trimming), label the entry as a stub:
     ```markdown
     > Stub: no usable definition extracted. See sources for context.
     ```

2. Add a minimum descriptive quality gate:
   - Entries that remain stubs after all fallbacks are collected in a `glossary_stubs` list in `index.yaml` so agents can identify gaps.

3. Add acceptance tests:
   - Entity with only a heading as context → glossary entry is labeled stub.
   - Entity with a `summary` field → glossary entry uses the summary.
   - Entity with a short `context` but useful `key_facts` → glossary entry uses the first fact sentence.

## Acceptance criteria

- No glossary entry uses a bare heading or fragment as its definition without a stub label.
- Summary and fact-sentence fallbacks are applied in the correct priority order.
- Stubs are surfaced in `index.yaml` for downstream gap detection.
