# 07 — Semantic Quality Metadata in KB Outputs

## Problem

`kb/index.yaml` validates structurally but gives equal weight to high-value concepts and low-value pseudo-entities. Downstream tools have no signal to distinguish them.

## Steps

1. Add a top-level `quality` block to `kb/index.yaml` at build time:

   ```yaml
   quality:
     entity_quality: warning        # ok | warning | low
     broken_wikilinks: 12
     skipped_low_confidence_entities: 42
     glossary_stubs: 7
   ```

2. Derive `entity_quality`:
   - `ok`: fewer than 5% of promoted entities were filtered or flagged.
   - `warning`: 5–25% filtered or flagged.
   - `low`: more than 25% filtered or flagged.

3. Add per-entity quality fields in the page entries:
   ```yaml
   - slug: mycenter
     type: product
     quality: ok
   - slug: about
     type: concept
     quality: low
   ```
   (Carry the quality flag from the extraction `quality.flags` field.)

4. Add an acceptance test: a KB built from a noisy extraction set → `index.yaml` quality block reports `warning` or `low`.

## Acceptance criteria

- `index.yaml` always includes a `quality` block with entity counts and thresholds.
- Per-entity quality flags are present and derived from upstream extraction quality.
- The overall quality grade is `low` when more than 25% of entities are flagged.
