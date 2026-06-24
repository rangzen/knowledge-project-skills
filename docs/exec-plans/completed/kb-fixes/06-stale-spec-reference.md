# 06 — Stale KB Spec Path Reference

## Problem

The KB schema reference in `SKILL.md` points to `../../docs/product-specs/kb.md`, which does not exist at that path. The normative schema is unreachable, mirroring the same documentation drift as the extract skill (ingestion-extract-fixes issue 05).

## Steps

1. Verify the actual path of `kb.md` from the skill directory.
2. Fix the relative path in `SKILL.md`.
3. Inline the minimum required schema rules directly in the skill folder so the skill is self-contained.
4. Add a broken-reference check (shared with the extract skill fix) that validates every relative link in `SKILL.md` files resolves to an existing file. This check should run as part of a CI step or the self-test suite.

## Acceptance criteria

- The KB `SKILL.md` schema reference resolves to an existing file.
- A broken-reference test catches future regressions for both `kb` and `extract` skills.
