from pathlib import Path

from conftest import DATA_DIR, run_preprocessor

FIXTURE = DATA_DIR / "pdf/sample-files.com dev-example.pdf"


def test_page_count():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    assert result["metadata"]["pages"] == 6


def test_all_page_markers_present():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    text = result["text"]
    for i in range(1, 7):
        assert f"[Page {i}]" in text


def test_table_entities_extracted():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    text = result["text"]
    assert "John Doe" in text
    assert "Jane Smith" in text
    assert "Alice Brown" in text


def test_table_structure_preserved():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    text = result["text"]
    assert "Developer" in text
    assert "Engineering" in text
    assert "Designer" in text


def test_source_ref():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    assert result["metadata"]["source_ref"].endswith("dev-example.pdf")
