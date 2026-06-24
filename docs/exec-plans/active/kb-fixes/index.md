# Plan: KB Fixes

Fixes for concrete issues found while building the KB from generated extraction files.
Source of truth: `caveats-kb.md` at repo root.

## Decisions locked in

| Topic | Decision |
|---|---|
| Wikilink fix | Fix the validator to parse `[[target\|label]]` correctly; keep alias links in generated output |
| Link policy | Document and test the basename-lookup assumption; enforce globally unique slugs |

## Issues

- [ ] [01 — Entity filtering before page generation](01-entity-filtering.md)
- [ ] [02 — Smarter entity resolution](02-entity-resolution.md)
- [x] [03 — Wikilink validator fix](03-wikilink-validation.md)
- [ ] [04 — Link generation consistency](04-link-generation.md)
- [ ] [05 — Glossary quality](05-glossary-quality.md)
- [ ] [06 — Stale KB spec path reference](06-stale-spec-reference.md)
- [ ] [07 — Semantic quality metadata in KB outputs](07-index-yaml-quality.md)
- [ ] [08 — Surface upstream extraction quality at build time](08-upstream-quality.md)

## Priority order

1. Issue 03 — fix wikilink validation (immediate noise reduction)
2. Issue 01 + 02 — entity filtering and resolution before page generation
3. Issue 05 — improve glossary so weak context does not become authoritative text
4. Issue 07 + 08 — add semantic quality reporting to outputs
5. Issue 04 — codify and test link generation policy
6. Issue 06 — fix the stale spec reference and add reference-validation tests
