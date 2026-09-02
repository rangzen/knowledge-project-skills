# Plan: Local PDF OCR fallback

**Goal**: Allow `kp-staging` to preprocess mixed and scanned PDFs locally when AnyDoc requires OCR.
**Status**: done
**Started**: 2026-09-02
**Completed**: 2026-09-02

## Steps

- [x] Review the issue, existing PDF passes, and current test coverage.
- [x] Add deterministic OCR caching and actionable dependency diagnostics.
- [x] Extend both PDF preprocessing passes and the skill instructions with OCR options.
- [x] Add focused unit tests and run the full relevant test suite.

## Progress log

- 2026-09-02: Confirmed the current primary pass is AnyDoc-only and the page-exact companion uses pypdf directly.
- 2026-09-02: Added local OCRmyPDF caching, explicit OCR options, metadata, and operational documentation.
- 2026-09-02: Corrected legacy tests to use `preprocess_pdf_pages.py` for page-marker assertions, matching the documented two-pass pipeline.
- 2026-09-02: Focused PDF/OCR suite passed (20 tests), skill-link validation passed, and the full suite passed 223 of 224 tests. The remaining failure is an unrelated pre-existing DOCX expectation for a `paragraphs` metadata field that its current preprocessor does not emit.

## Decision log

- 2026-09-02: Put the fallback in `preprocess_pdf.py` and share its OCR helper with `preprocess_pdf_pages.py` so callers can use the same derivative for both passes without mutating raw sources.
- 2026-09-02: Use the source SHA-256 plus normalized OCR configuration in the cache key, keeping derivatives reproducible and invalidating them when source bytes or options change.
