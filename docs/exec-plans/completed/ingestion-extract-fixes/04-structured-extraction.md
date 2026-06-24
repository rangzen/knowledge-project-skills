# 04 — Structured Extraction Pipeline

## Problem

The `extract` skill provides `extract_pdf.py` for text extraction but has no bundled implementation for the structured extraction step that produces `extractions/<source-id>.json`. Agents must invent this step, producing incompatible outputs.

## Decision

Ship a two-stage pipeline:

1. **Format preprocessor**: format-specific script that reads the source file and outputs clean, LLM-ready text (or structured content). See issue 06 for the full format list.
2. **LLM extractor**: a single common script (`extract_llm.py`) that sends preprocessed content to the LLM and writes a compliant `extractions/<source-id>.json`.

The LLM extraction targets: entities, events, topics, key facts, dates, and summaries.

## Steps

1. Design the preprocessor interface:
   - Input: path to source file
   - Output: a JSON payload sent to `extract_llm.py` containing `{ "text": "...", "metadata": { "format": "...", "pages": N } }`
   - Each format has its own preprocessor script (see issue 06).

2. Write `extract_llm.py`:
   - Accepts preprocessor output (file or stdin).
   - Calls the LLM with a prompt template that requests: `summary`, `entities` (with `name`, `type`, `aliases`, `context`), `events`, `topics`, `key_facts`, `dates`.
   - Writes compliant JSON to `extractions/<source-id>.json`.
   - Validates output against the schema before writing (fail loudly on malformed LLM output).

3. Wire the pipeline in the `extract` skill:
   - Detect format (see issue 06).
   - Call the matching preprocessor.
   - Pipe output to `extract_llm.py`.

4. Update `SKILL.md` to document the two-stage pipeline and each script's interface.

5. Add an end-to-end acceptance test: one PDF and one DOCX → both produce valid `extractions/*.json`.

## Acceptance criteria

- Running `extract` on any supported format produces `extractions/<source-id>.json` without agent invention.
- Output JSON validates against the extraction schema.
- Pipeline fails loudly (non-zero exit, clear error message) when the LLM returns malformed output.
