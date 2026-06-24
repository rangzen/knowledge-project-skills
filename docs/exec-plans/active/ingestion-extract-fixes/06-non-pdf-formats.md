# 06 — Format-Specific Extraction Preprocessors

## Problem

The skill implied universal support for "all source types" but provided no format-specific extraction guidance. A DOCX file, for example, is a zipped XML container and cannot be read directly as plain text.

## Decision

Ship one preprocessor script per supported format. Each script outputs clean, LLM-ready text that feeds into `extract_llm.py` (see issue 04).

## Supported formats

| Format | Preprocessor | Notes |
|---|---|---|
| PDF | `preprocess_pdf.py` | Already exists as `extract_pdf.py`; adapt to interface |
| DOCX | `preprocess_docx.py` | Use `python-docx` to extract paragraphs and tables |
| Excel (xlsx/xls) | `preprocess_excel.py` | Use `openpyxl`; emit sheet names + cell ranges as structured text |
| Markdown | `preprocess_text.py` | Read as-is; strip front matter if present |
| Plain text | `preprocess_text.py` | Shared with markdown |
| Mermaid | `preprocess_text.py` | Read as-is; tag as diagram source in metadata |
| Obsidian vault | `preprocess_obsidian.py` | Flatten wikilinks to plain text; strip `[[` / `]]` syntax; emit one doc per note file |
| JSON / CSV | `preprocess_structured.py` | Serialize as readable table or key-value text for LLM consumption |

## Steps

1. Define the preprocessor interface contract in `SKILL.md`:
   - Input: source file path
   - Output (stdout or file): `{ "text": "...", "format": "...", "metadata": { ... } }`
2. Implement each preprocessor listed above.
3. Add format detection logic in the `extract` skill (by extension and MIME sniff).
4. If a file's format is unsupported, fail with a clear error: `Unsupported format: .xyz — supported: pdf, docx, xlsx, md, txt, mermaid, json, csv`.
5. Add one acceptance test per format: valid input → non-empty text output.

## Acceptance criteria

- Every format in the table above has a working preprocessor.
- Unsupported formats produce a clear, actionable error rather than garbled output.
- Format detection is based on content sniffing, not only extension.
