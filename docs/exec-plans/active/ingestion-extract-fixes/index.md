# Plan: Ingestion + Extract Fixes

Fixes for concrete issues found while exercising `init`, `ingestion`, and `extract` in a real project run.
Source of truth: `caveats-extract.md` at repo root.

## Decisions locked in

| Topic | Decision |
|---|---|
| Directory input | Recursive per-file; warn + confirm when file count exceeds threshold (default 50) |
| Extract pipeline | Format detect → format-specific preprocessor → common LLM extraction call → JSON |
| Metadata model | One source ID per file; keep schema flat (no `files[]` array) |
| Wikilink aliases | Fix the validator, not the generator (covered in kb-fixes plan) |

## Issues

- [ ] [01 — Directory ingestion semantics](01-directory-ingestion.md)
- [ ] [02 — Recursive ingestion + duplicate handling](02-recursive-ingestion.md)
- [ ] [03 — Metadata model one-source-per-file invariant](03-metadata-model.md)
- [x] [04 — Structured extraction pipeline](04-structured-extraction.md)
- [x] [05 — Broken spec path reference in extract skill](05-broken-spec-reference.md)
- [ ] [06 — Format-specific extraction for non-PDF types](06-non-pdf-formats.md)
- [ ] [07 — Extraction quality guardrails](07-quality-guardrails.md)
- [ ] [08 — Richer extraction status (replace `extracted: true`)](08-extraction-status.md)

## Priority order

1. Issue 04 — unblocks end-to-end extract runs
2. Issue 01 + 02 — define and implement directory ingestion
3. Issue 06 — ships preprocessors for all supported formats
4. Issue 05 — fix broken documentation reference
5. Issue 03 — codify the one-source-per-file invariant
6. Issue 07 + 08 — quality gates and richer status metadata
