from conftest import DATA_DIR, run_preprocessor


def test_excel_metadata_fields():
    result = run_preprocessor("preprocess_excel.py", DATA_DIR / "excel/sample.xlsx")
    meta = result["metadata"]
    assert meta["format"] == "xlsx"
    assert meta["source_ref"].endswith("sample.xlsx")
    assert meta["sheets"] == 2
    assert meta["rows"] > 0


def test_excel_text_extracted():
    result = run_preprocessor("preprocess_excel.py", DATA_DIR / "excel/sample.xlsx")
    assert "Alice" in result["text"]
    assert "Paris" in result["text"]


def test_excel_sheet_names_in_text():
    result = run_preprocessor("preprocess_excel.py", DATA_DIR / "excel/sample.xlsx")
    assert "[Sheet: People]" in result["text"]
    assert "[Sheet: Events]" in result["text"]


def test_excel_second_sheet_data():
    result = run_preprocessor("preprocess_excel.py", DATA_DIR / "excel/sample.xlsx")
    assert "Acquisition" in result["text"]
