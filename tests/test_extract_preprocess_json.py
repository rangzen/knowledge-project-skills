from conftest import DATA_DIR, run_preprocessor


def test_json_array_metadata():
    result = run_preprocessor("preprocess_json.py", DATA_DIR / "json/array.json")
    meta = result["metadata"]
    assert meta["format"] == "json"
    shape = meta["shape"]
    assert shape["_array_length"] == 3
    item = shape["_item_shape"]
    assert item["name"] == "string"
    assert item["age"] == "integer"
    assert item["active"] == "boolean"


def test_json_array_nested_shape():
    result = run_preprocessor("preprocess_json.py", DATA_DIR / "json/array.json")
    item = result["metadata"]["shape"]["_item_shape"]
    assert item["tags"]["_array_length"] == 2
    assert item["tags"]["_item_shape"] == "string"


def test_json_object_metadata():
    result = run_preprocessor("preprocess_json.py", DATA_DIR / "json/object.json")
    shape = result["metadata"]["shape"]
    assert shape["project"] == "string"
    assert shape["version"] == "string"
    assert isinstance(shape["settings"], dict)
    assert "max_sources" in shape["settings"]


def test_json_content_passthrough():
    result = run_preprocessor("preprocess_json.py", DATA_DIR / "json/array.json")
    assert "Alice" in result["text"]


def test_json_missing_file_exits_nonzero():
    import subprocess
    from conftest import SCRIPTS_DIR
    r = subprocess.run(
        ["uv", "run", str(SCRIPTS_DIR / "preprocess_json.py"), "/tmp/does_not_exist.json"],
        capture_output=True,
    )
    assert r.returncode != 0
