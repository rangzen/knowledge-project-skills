# Local Development

## Running tests

```bash
uv run pytest
```

Run a specific file:

```bash
uv run pytest tests/test_kb_glossary_quality.py
```

Run tests matching a name pattern:

```bash
uv run pytest -k "glossary"
```

## Test fixtures

Binary fixtures (PDF, DOCX, XLSX) are generated on first run via `tests/generate_fixtures.py`. The `conftest.py` session fixture handles this automatically -- no manual step needed.

To regenerate manually:

```bash
uv run --group dev tests/generate_fixtures.py
```

## Dependencies

Install dev dependencies with:

```bash
uv sync --group dev
```
