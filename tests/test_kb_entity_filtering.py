"""Tests for filter_entities() and _load_stoplist() in kb_build.py."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/kb/scripts/kb_build.py"
spec = importlib.util.spec_from_file_location("kb_build", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

filter_entities = _mod.filter_entities
_load_stoplist = _mod._load_stoplist
_candidate_stoplist_entries = _mod._candidate_stoplist_entries


def _entity(name: str, etype: str = "concept", sources: list[str] | None = None) -> dict:
    return {"name": name, "type": etype, "_sources": sources or ["src-1"]}


def _project(tmp_path: Path, stoplist_lines: list[str] | None = None) -> Path:
    (tmp_path / ".knowledge-project").write_text("{}")
    config_dir = tmp_path / "kb" / "config"
    config_dir.mkdir(parents=True)
    if stoplist_lines is not None:
        (config_dir / "entity_stoplist.txt").write_text("\n".join(stoplist_lines))
    return tmp_path


class TestLoadStoplist:
    def test_missing_file_returns_empty(self, tmp_path):
        (tmp_path / ".knowledge-project").write_text("{}")
        (tmp_path / "kb").mkdir()
        assert _load_stoplist(tmp_path) == set()

    def test_loads_entries(self, tmp_path):
        root = _project(tmp_path, ["about", "access", "# comment", "", "Overview"])
        result = _load_stoplist(root)
        assert "about" in result
        assert "access" in result
        assert "overview" in result
        assert "# comment" not in result
        assert "" not in result

    def test_case_insensitive_load(self, tmp_path):
        root = _project(tmp_path, ["About", "ACCESS"])
        result = _load_stoplist(root)
        assert "about" in result
        assert "access" in result


class TestFilterEntities:
    def test_stoplist_drops_entity(self, tmp_path):
        root = _project(tmp_path, ["about"])
        entities = [_entity("About"), _entity("MyCenter")]
        kept, filtered = filter_entities(entities, root)
        assert filtered == 1
        assert len(kept) == 1
        assert kept[0]["name"] == "MyCenter"

    def test_stoplist_check_is_case_insensitive(self, tmp_path):
        root = _project(tmp_path, ["about"])
        entities = [_entity("ABOUT"), _entity("About"), _entity("about")]
        kept, filtered = filter_entities(entities, root)
        assert filtered == 3
        assert kept == []

    def test_doc_code_without_type_dropped(self, tmp_path):
        root = _project(tmp_path)
        entities = [_entity("AD31971-EN", etype="concept")]
        kept, filtered = filter_entities(entities, root)
        assert filtered == 1
        assert kept == []

    def test_doc_code_with_document_type_kept(self, tmp_path):
        root = _project(tmp_path)
        entities = [_entity("AD31971-EN", etype="document")]
        kept, filtered = filter_entities(entities, root)
        assert filtered == 0
        assert len(kept) == 1

    def test_doc_code_regex_matches_pattern(self, tmp_path):
        root = _project(tmp_path)
        cases = ["AB31", "X100-EN", "AD31971-EN", "V2DOC-REF"]
        for name in cases:
            entities = [_entity(name, etype="concept")]
            _, filtered = filter_entities(entities, root)
            assert filtered == 1, f"{name!r} should be filtered as a doc code"

    def test_doc_code_regex_spares_plain_words(self, tmp_path):
        root = _project(tmp_path)
        cases = ["MyCenter", "USA", "NATO", "Overview"]
        for name in cases:
            entities = [_entity(name, etype="organization")]
            _, filtered = filter_entities(entities, root)
            assert filtered == 0, f"{name!r} should not be filtered as a doc code"

    def test_min_source_count_filters_single_source(self, tmp_path):
        root = _project(tmp_path)
        entities = [_entity("MyCenter", sources=["src-1"])]
        kept, filtered = filter_entities(entities, root, min_source_count=2)
        assert filtered == 1
        assert kept == []

    def test_min_source_count_promotes_multi_source(self, tmp_path):
        root = _project(tmp_path)
        entities = [_entity("MyCenter", sources=["src-1", "src-2"])]
        kept, filtered = filter_entities(entities, root, min_source_count=2)
        assert filtered == 0
        assert len(kept) == 1

    def test_default_min_source_count_keeps_all(self, tmp_path):
        root = _project(tmp_path)
        entities = [_entity("MyCenter", sources=["src-1"])]
        kept, filtered = filter_entities(entities, root)
        assert filtered == 0
        assert len(kept) == 1

class TestCandidateStoplistEntries:
    def test_all_lowercase_single_word_is_candidate(self):
        entities = [_entity("overview"), _entity("MyCenter")]
        assert _candidate_stoplist_entries(entities) == ["overview"]

    def test_proper_noun_excluded(self):
        assert _candidate_stoplist_entries([_entity("MyCenter")]) == []

    def test_multi_word_excluded(self):
        assert _candidate_stoplist_entries([_entity("getting started")]) == []

    def test_all_uppercase_excluded(self):
        assert _candidate_stoplist_entries([_entity("NATO")]) == []

    def test_returns_sorted_deduped(self):
        entities = [_entity("zebra"), _entity("apple"), _entity("apple")]
        assert _candidate_stoplist_entries(entities) == ["apple", "zebra"]


    def test_no_stoplist_file_skips_stoplist_filter(self, tmp_path):
        (tmp_path / ".knowledge-project").write_text("{}")
        (tmp_path / "kb").mkdir()
        entities = [_entity("About"), _entity("Access")]
        kept, filtered = filter_entities(entities, tmp_path)
        assert filtered == 0
        assert len(kept) == 2
