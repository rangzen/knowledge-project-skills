# Plan: Revise the local PDF OCR fallback

## Status

Proposed after a local integration test showed that the initial OCR fallback is not sufficient for every scanned or hybrid PDF.

## Problem

The current PDF fallback is:

```text
AnyDoc fails because OCR is required
  -> OCRmyPDF creates a local derivative
  -> AnyDoc converts the derivative
```

This assumes that adding a Tesseract text layer makes a PDF acceptable to AnyDoc. That assumption is not reliable.

In an anonymized integration test using a fully scanned, 28-page technical manual:

1. AnyDoc rejected the original PDF as OCR-required.
2. OCRmyPDF completed successfully and the page-exact `pypdf` pass extracted usable text from the local derivative.
3. AnyDoc still rejected the derivative, first for a subset of pages when OCRmyPDF used `--skip-text` and then for every page after a separate `--force-ocr` experiment.

The forced experiment also rasterized several vector pages and increased the output PDF size substantially. It is therefore not a safe default retry strategy.

## Research

AnyDoc documents itself as a local converter for text-based PDFs, not as an OCR engine. Its own skill states that scanned and image-only PDFs require OCR and are unsupported locally; its hosted Parse product provides OCR separately.

- [AnyDoc conversion skill](https://github.com/firecrawl/anydoc/blob/main/skills/convert-documents-to-markdown/SKILL.md)
- [AnyDoc README](https://github.com/firecrawl/anydoc)

The behavior also fits an open `pdf-inspector` report that identifies false OCR-required classifications caused by page-level text-coverage decisions. The exact classification rule for this document has not been independently proven, so this is an evidence-backed inference rather than a confirmed root cause.

- [pdf-inspector issue #213](https://github.com/firecrawl/pdf-inspector/issues/213)

## Decision

Do not rely on `OCRmyPDF -> AnyDoc` as the final fallback.

Instead, use this pipeline:

```text
AnyDoc primary conversion
  -> success: structured Markdown (current behavior)
  -> OCR-required failure:
       OCRmyPDF local derivative
         -> pypdf text extraction from the derivative
         -> primary fallback payload with `structured: false`
         -> same pypdf text for the page-citable companion pass
```

The agent extraction stage can still create entities, key facts, and page citations from the fallback text. It loses AnyDoc's heading/table reconstruction, so the metadata must make that trade-off visible instead of presenting the result as structured Markdown.

## Proposed implementation

### 1. Add a pypdf primary fallback

Extend `preprocess_pdf.py` so that, after an OCR-required AnyDoc failure and successful OCR derivative creation, it calls a shared pypdf text extractor rather than calling AnyDoc a second time.

The output should include:

```json
{
  "text": "[Page 1] ...",
  "metadata": {
    "format": "pdf",
    "source_ref": "sources/<source-id>/<file>.pdf",
    "pages": 28,
    "paginated": true,
    "structured": false,
    "fallback": "pypdf-ocr-text",
    "ocr_applied": true
  }
}
```

Keep the original source reference and reuse the existing OCR provenance fields. The text can be page-marked in this primary fallback because traceability matters more than Markdown layout when AnyDoc is unavailable.

### 2. Keep the existing structured path unchanged

Text-only PDFs must continue to use AnyDoc and report `structured: true` (or omit the field for compatibility). The new branch must run only for an OCR-required AnyDoc failure.

### 3. Reuse, do not duplicate, page extraction

Extract the common pypdf page-reading logic from `preprocess_pdf_pages.py` into a shared helper. Both the primary fallback and the companion pass should use the same OCR derivative, preserve page indices, and avoid another OCR run.

### 4. Clarify OCR modes

- `--ocr auto`: attempt AnyDoc first; on an OCR-required failure, create/reuse the derivative and use pypdf OCR text as the primary fallback.
- `--ocr off`: preserve current AnyDoc-only failure behavior.
- `--ocr force`: create/reuse an OCR derivative before preprocessing, then use pypdf OCR text directly. Do not force-rasterize every page unless an explicit advanced option requests it.

`--skip-text` remains the appropriate default OCRmyPDF option. A forced-rasterization retry should not be part of the normal pipeline because it can degrade vector pages and inflate output size.

### 5. Update skill guidance

Update `skills/kp-staging/SKILL.md` to state that OCR fallback preserves text and page citations but may not preserve headings, tables, or document layout. The extraction agent should be instructed to retain headings and tables only when the fallback text supports them.

## Tests to add

Add integration-oriented tests in addition to the existing mocked OCR-cache tests:

1. **Text-only PDF:** AnyDoc succeeds; OCR and pypdf fallback are not invoked.
2. **OCR-required PDF:** mock AnyDoc to raise an OCR-required error, mock OCRmyPDF derivative creation, and verify that the primary output uses the pypdf fallback with `structured: false`.
3. **AnyDoc rejects derivative:** explicitly model the observed failure. Verify the pipeline does not retry AnyDoc after OCR and still returns usable pypdf text.
4. **Companion reuse:** verify both primary fallback and paginated companion use the same cached derivative and preserve page numbers.
5. **Missing dependencies:** retain actionable diagnostics and no source mutation.
6. **Cache invalidation:** retain the source-hash and OCR-config cache key behavior.
7. **Sensitive source:** keep derivatives out of Git and avoid logging extracted contents.

Use generated or public fixtures only. Do not add customer documents, repository names, source-system names, credentials, or other identifying content to tests, fixtures, documentation, or commit messages.

## Acceptance criteria

- A locally OCRed PDF produces a valid primary preprocessing payload even when AnyDoc rejects both the original and OCR derivative.
- That payload retains the original `source_ref`, OCR provenance, page markers, and `structured: false` metadata.
- The page-exact companion uses the same derivative without additional OCR work.
- Existing text-only PDF output is unchanged.
- Raw files in `sources/` are never modified.
- The documentation states the reduced structural fidelity of the fallback.

## Follow-up

If high-fidelity local Markdown reconstruction for scanned PDFs becomes a requirement, evaluate a separate local OCR/layout parser behind an explicit optional dependency. That is a distinct product decision from reliable text extraction and should not be hidden behind the AnyDoc fallback.
