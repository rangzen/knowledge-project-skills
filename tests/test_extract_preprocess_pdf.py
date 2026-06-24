from conftest import DATA_DIR, run_preprocessor


def test_pdf_metadata_fields():
    result = run_preprocessor("preprocess_pdf.py", DATA_DIR / "pdf/sample.pdf")
    meta = result["metadata"]
    assert meta["format"] == "pdf"
    assert meta["source_ref"].endswith("sample.pdf")
    assert meta["pages"] == 2


def test_pdf_text_extracted():
    result = run_preprocessor("preprocess_pdf.py", DATA_DIR / "pdf/sample.pdf")
    assert len(result["text"]) > 0
    assert "Alice" in result["text"]
    assert "Acme Corp" in result["text"]


def test_pdf_page_markers():
    result = run_preprocessor("preprocess_pdf.py", DATA_DIR / "pdf/sample.pdf")
    assert "[Page 1]" in result["text"]
    assert "[Page 2]" in result["text"]
