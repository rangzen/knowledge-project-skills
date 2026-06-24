from pathlib import Path

from conftest import DATA_DIR, run_preprocessor


def test_csv_metadata_fields():
    result = run_preprocessor("preprocess_csv.py", DATA_DIR / "csv/sample.csv")
    meta = result["metadata"]
    assert meta["format"] == "csv"
    assert meta["source_ref"].endswith("sample.csv")
    assert meta["column_count"] == 5
    assert meta["columns"] == ["name", "age", "city", "score", "active"]
    assert meta["row_count"] == 10


def test_csv_content_passthrough():
    result = run_preprocessor("preprocess_csv.py", DATA_DIR / "csv/sample.csv")
    assert "Alice" in result["text"]
    assert "name,age,city" in result["text"]


def test_csv_numeric_profile():
    result = run_preprocessor("preprocess_csv.py", DATA_DIR / "csv/sample.csv")
    profile = {col["name"]: col for col in result["metadata"]["profile"]}
    assert profile["age"]["type"] == "numeric"
    assert profile["age"]["min"] == 25.0
    assert profile["age"]["max"] == 35.0
    assert profile["score"]["type"] == "numeric"


def test_csv_boolean_profile():
    result = run_preprocessor("preprocess_csv.py", DATA_DIR / "csv/sample.csv")
    profile = {col["name"]: col for col in result["metadata"]["profile"]}
    assert profile["active"]["type"] == "boolean"


def test_csv_enum_detection():
    result = run_preprocessor("preprocess_csv.py", DATA_DIR / "csv/sample.csv")
    profile = {col["name"]: col for col in result["metadata"]["profile"]}
    assert "enum" in profile["city"]
    assert set(profile["city"]["enum"]) == {"Paris", "Lyon", "Berlin"}


def test_csv_missing_file_exits_nonzero():
    import subprocess
    from conftest import SCRIPTS_DIR
    r = subprocess.run(
        ["uv", "run", str(SCRIPTS_DIR / "preprocess_csv.py"), "/tmp/does_not_exist.csv"],
        capture_output=True,
    )
    assert r.returncode != 0
