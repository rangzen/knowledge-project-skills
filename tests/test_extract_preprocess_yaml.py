from conftest import DATA_DIR, run_preprocessor


def test_yaml_metadata_fields():
    result = run_preprocessor("preprocess_yaml.py", DATA_DIR / "yaml/config.yaml")
    meta = result["metadata"]
    assert meta["format"] == "yaml"
    assert meta["source_ref"].endswith("config.yaml")
    assert "shape" in meta


def test_yaml_top_level_shape():
    result = run_preprocessor("preprocess_yaml.py", DATA_DIR / "yaml/config.yaml")
    shape = result["metadata"]["shape"]
    assert shape["project"] == "string"
    assert shape["version"] == "string"
    assert isinstance(shape["pipeline"], dict)


def test_yaml_nested_shape():
    result = run_preprocessor("preprocess_yaml.py", DATA_DIR / "yaml/config.yaml")
    shape = result["metadata"]["shape"]
    assert "extract" in shape["pipeline"]
    assert "model" in shape["pipeline"]["extract"]


def test_yaml_array_shape():
    result = run_preprocessor("preprocess_yaml.py", DATA_DIR / "yaml/config.yaml")
    shape = result["metadata"]["shape"]
    assert shape["sources"]["_array_length"] == 2


def test_yaml_content_passthrough():
    result = run_preprocessor("preprocess_yaml.py", DATA_DIR / "yaml/config.yaml")
    assert "knowledge-project-skills" in result["text"]
    assert "claude-sonnet" in result["text"]
