# 03 — Wikilink Validator Fix

## Problem

`validate_wikilinks()` does not parse `[[target|label]]` alias syntax correctly. It validates against the display label instead of the link target, producing 298 false broken-link warnings that drown out real issues.

## Decision

Fix the validator to handle both `[[target]]` and `[[target|label]]`. Keep alias links in generated output — they are semantically richer.

## Steps

1. Update the wikilink parsing regex in `validate_wikilinks()`:
   - Current (broken): matches the full `[[...]]` content as the page name.
   - Fixed: split on `|` and validate only the left-hand side (the target slug).

2. Handle edge cases:
   - `[[target]]` — validate `target`.
   - `[[target|label]]` — validate `target`, ignore `label`.
   - `[[target|label with spaces]]` — same as above.
   - `[[Glossary#Section]]` — validate `Glossary` (strip anchor).

3. Add unit tests covering all four cases above, plus:
   - A link to a slugified name with punctuation (e.g. `[[a-d|A&D]]`).
   - A broken link where the target genuinely does not exist.

4. Re-run validation after the fix and confirm the warning count drops to real broken links only.

## Acceptance criteria

- `[[slug|Display Name]]` does not produce a false broken-link warning.
- Genuinely missing targets are still reported.
- All four edge-case tests pass.
