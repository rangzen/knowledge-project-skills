# 08 — Richer Extraction Status (Replace `extracted: true`)

## Problem

`extracted: true` in `.meta.json` cannot distinguish between: complete extraction, partial extraction, low-quality extraction, or outdated extraction after extractor improvements.

## Decision

Replace the boolean with a structured `extraction` object.

## New schema

```json
{
  "extraction": {
    "status": "complete",
    "extractor_version": "1.0.0",
    "extracted_at": "2026-06-24T10:00:00Z",
    "quality": "warning"
  }
}
```

Valid `status` values: `"complete"`, `"partial"`, `"failed"`, `"skipped"`.
Valid `quality` values: `"ok"`, `"warning"`, `"low"`.

## Steps

1. Update `ingest.py` to write the new `extraction` object instead of `extracted: true` when extraction completes.
2. Update `extract_llm.py` to set `status`, `extractor_version`, and `extracted_at` after a successful run.
3. Set `quality` from the quality check results (see issue 07).
4. Update any code that reads `extracted: true` (e.g. skip-already-extracted logic) to check `extraction.status == "complete"`.
5. Add a migration note in `SKILL.md`: existing sources with `extracted: true` are treated as `status: "complete", quality: "unknown"`.
6. Support `--force` re-extraction: rerun even when `status == "complete"`, updating `extracted_at`.

## Acceptance criteria

- `.meta.json` no longer contains a bare `extracted: true`.
- `extraction.status` is set correctly for complete, failed, and force-rerun cases.
- `--force` flag triggers re-extraction regardless of current status.
