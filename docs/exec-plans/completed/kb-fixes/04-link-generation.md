# 04 — Link Generation Consistency

## Problem

`index.md` generates links as `[[slug|Name]]` while pages live in typed subdirectories (`products/slug.md`, `concepts/slug.md`). Resolution depends on a global basename lookup, which is implicit and breaks on slug collisions.

## Decision

Keep basename-based linking for now (it matches Obsidian's resolution model), but enforce globally unique slugs across all entity types and document the assumption explicitly.

## Steps

1. Add a slug-collision check in `kb_build.py`:
   - Before writing any page, verify the slug is globally unique across all entity types.
   - If a collision is detected, disambiguate by appending the type (`slug-product`, `slug-concept`) and log a warning.

2. Document the basename-lookup assumption in `SKILL.md`:
   - "Links use bare slugs. Slugs must be globally unique across all entity subdirectories. Obsidian resolves by basename; other consumers must implement equivalent lookup."

3. Add an acceptance test:
   - Two entities with the same name but different types → disambiguated slugs, no collision, warning logged.

## Acceptance criteria

- Slug collisions are detected and disambiguated before page generation.
- The basename-lookup assumption is documented in `SKILL.md`.
- A collision test exists and passes.
