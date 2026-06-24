from pathlib import Path

from conftest import DATA_DIR, run_preprocessor

FIXTURE = DATA_DIR / "pdf/sample-files.com sample-5-page-pdf-a4-size.pdf"


def test_page_count():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    assert result["metadata"]["pages"] == 5


def test_all_page_markers_present():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    text = result["text"]
    for i in range(1, 6):
        assert f"[Page {i}]" in text


def test_company_entities_extracted():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    text = result["text"]
    assert "Innovative Tech Solutions" in text
    assert "SmartTech Co." in text
    assert "HomeGenius" in text
    assert "ConnectAll" in text


def test_person_entity_extracted():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    assert "Alex Johnson" in result["text"]


def test_market_data_extracted():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    text = result["text"]
    assert "135.3 billion" in text
    assert "11.6%" in text


def test_source_ref():
    result = run_preprocessor("preprocess_pdf.py", FIXTURE)
    assert result["metadata"]["source_ref"].endswith("sample-5-page-pdf-a4-size.pdf")
