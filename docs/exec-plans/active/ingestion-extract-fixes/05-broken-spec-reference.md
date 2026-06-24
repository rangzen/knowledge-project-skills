# 05 — Broken Spec Path Reference in Extract Skill

## Problem

The extraction schema reference in `SKILL.md` points to `../../docs/product-specs/extract.md`, which does not exist at that path, making the normative schema unreachable.

## Steps

1. Verify the actual path of the extract product spec (likely `docs/product-specs/extract.md` from the repo root).
2. Fix the relative path in `SKILL.md`.
3. Copy or inline the minimum required schema fields directly in the skill folder so the skill is self-contained even if the spec moves.
4. Add a CI check (or a smoke test in the self-test suite, see issue 09 in caveats) that validates every relative link in each `SKILL.md` resolves to an existing file.

## Acceptance criteria

- The schema reference link in `SKILL.md` resolves to an existing file.
- A broken-reference check exists and would catch a future regression.
