from conftest import DATA_DIR, run_preprocessor


def test_docx_metadata_fields():
    result = run_preprocessor("preprocess_docx.py", DATA_DIR / "docx/sample.docx")
    meta = result["metadata"]
    assert meta["format"] == "docx"
    assert meta["source_ref"].endswith("sample.docx")
    assert meta["paragraphs"] > 0
    assert meta["tables"] == 1


def test_docx_text_extracted():
    result = run_preprocessor("preprocess_docx.py", DATA_DIR / "docx/sample.docx")
    assert "Alice" in result["text"]
    assert "Acme Corp" in result["text"]


def test_docx_table_extracted():
    result = run_preprocessor("preprocess_docx.py", DATA_DIR / "docx/sample.docx")
    assert "CEO" in result["text"]
    assert "CTO" in result["text"]
