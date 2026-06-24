# 07 — Extraction Quality Guardrails

## Problem

A heuristic extraction pass produced structurally valid JSON but low-quality content: generic entities, weak summaries, and one source with zero entities. Downstream KB generation treats these as complete.

## Steps

1. Add a post-extraction quality check step in `extract_llm.py` (or a separate `validate_extraction.py`):
   - Minimum summary length: reject summaries under 50 characters.
   - Minimum entity count: warn if a text-bearing source has fewer than 2 non-noisy entities.
   - Duplicate entity filter: deduplicate entities by normalized name before writing.
   - Low-text-coverage detection: if the preprocessor returned fewer than 100 tokens of text, flag the source.

2. Add `quality` fields to the extraction JSON output:
   ```json
   {
     "quality": {
       "flags": ["low_entity_count"],
       "warnings": ["Summary is shorter than expected for a 40-page document."],
       "text_coverage": 0.82
     }
   }
   ```

3. Print a quality summary after each extraction run:
   ```
   Extraction complete.
   Warnings: 2 sources with low entity count, 1 source with low text coverage.
   ```

4. Add acceptance tests:
   - Empty text input → `quality.flags` includes `"no_text"`.
   - Source with 0 entities → warning is emitted, extraction still written (not silently dropped).

## Acceptance criteria

- Every extraction JSON includes a `quality` block.
- Low-quality extractions are flagged and warned about, not silently accepted.
- Duplicate entities are filtered before output.
