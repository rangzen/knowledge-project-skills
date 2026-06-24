# 02 — Smarter Entity Resolution

## Problem

`resolve_entities()` merges by lowercase name only. It does not handle type differences, aliases, document-code variants, or near-duplicates, causing unrelated things to merge and related things to stay split.

## Steps

1. Extend `resolve_entities()` with type-aware merging:
   - Two entities with the same name but different types (e.g. `product` vs `concept`) are not merged automatically; log a conflict for manual review.

2. Add alias normalization:
   - If entity A has an alias that matches the name of entity B, merge B into A.
   - Preserve the full alias list on the merged entity.

3. Add document-code handling:
   - Entities that resolve to a known document code are either dropped (see issue 01) or consolidated under a `document` type page.

4. Add a confidence threshold gate:
   - If extraction output includes a confidence score per entity, skip entities below the configured threshold (default: 0 — no filtering, so existing behavior is preserved until threshold is set).

5. Add acceptance tests:
   - `MyCenter` (product) + `mycenter` (concept) → conflict logged, not silently merged.
   - Entity A with alias `B` + entity B → merged into A with alias preserved.

## Acceptance criteria

- Near-duplicates with type conflicts are flagged rather than silently merged.
- Alias-based resolution collapses the correct entities.
- Confidence threshold is respected when set.
