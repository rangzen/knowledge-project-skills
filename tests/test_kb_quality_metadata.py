"""Tests for quality metadata in kb_build.py (issues 07 and 08)."""
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/kb/scripts/kb_build.py"
spec = importlib.util.spec_from_file_location("kb_build", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

scan_extraction_quality = _mod.scan_extraction_quality
_extraction_quality_map = _mod._extraction_quality_map
_entity_quality = _mod._entity_quality
_overall_entity_quality = _mod._overall_entity_quality
_build_overall_quality = _mod._build_overall_quality
write_build_report = _mod.write_build_report
write_index_yaml = _mod.write_index_yaml


def _ext(source_id: str, flags: list[str] | None = None, entity_count: int = 3, coverage: float | None = None) -> dict:
    entities = [
        {"name": f"Entity{i}", "type": "concept", "context": "x", "confidence": 1.0}
        for i in range(entity_count)
    ]
    quality: dict = {"flags": flags or [], "warnings": [], "text_coverage": coverage}
    return {"source_id": source_id, "schema_version": "1", "entities": entities, "quality": quality}


def _entity(name: str, sources: list[str] | None = None) -> dict:
    return {"name": name, "type": "concept", "_sources": sources or ["src-1"], "aliases": []}


# ---------------------------------------------------------------------------
# scan_extraction_quality
# ---------------------------------------------------------------------------

class TestScanExtractionQuality:
    def test_clean_extractions_all_zero(self):
        exts = [_ext("src-1"), _ext("src-2")]
        result = scan_extraction_quality(exts)
        assert result["total"] == 2
        assert result["sources_with_warnings"] == 0
        assert result["sources_with_no_entities"] == 0
        assert result["sources_with_low_coverage"] == 0

    def test_flags_counted_as_warnings(self):
        exts = [_ext("src-1", flags=["low_summary"]), _ext("src-2")]
        result = scan_extraction_quality(exts)
        assert result["sources_with_warnings"] == 1

    def test_zero_entities_counted(self):
        exts = [_ext("src-1", entity_count=0), _ext("src-2")]
        result = scan_extraction_quality(exts)
        assert result["sources_with_no_entities"] == 1

    def test_low_coverage_counted(self):
        exts = [_ext("src-1", coverage=0.3), _ext("src-2", coverage=0.9)]
        result = scan_extraction_quality(exts)
        assert result["sources_with_low_coverage"] == 1

    def test_coverage_exactly_05_not_low(self):
        exts = [_ext("src-1", coverage=0.5)]
        result = scan_extraction_quality(exts)
        assert result["sources_with_low_coverage"] == 0

    def test_empty_extractions(self):
        result = scan_extraction_quality([])
        assert result["total"] == 0
        assert result["sources_with_warnings"] == 0


# ---------------------------------------------------------------------------
# _extraction_quality_map
# ---------------------------------------------------------------------------

class TestExtractionQualityMap:
    def test_no_flags_is_ok(self):
        exts = [_ext("src-1")]
        assert _extraction_quality_map(exts) == {"src-1": "ok"}

    def test_single_flag_is_warning(self):
        exts = [_ext("src-1", flags=["low_summary"])]
        assert _extraction_quality_map(exts) == {"src-1": "warning"}

    def test_no_text_flag_is_low(self):
        exts = [_ext("src-1", flags=["no_text"])]
        assert _extraction_quality_map(exts) == {"src-1": "low"}

    def test_two_flags_is_low(self):
        exts = [_ext("src-1", flags=["low_summary", "low_entity_count"])]
        assert _extraction_quality_map(exts) == {"src-1": "low"}


# ---------------------------------------------------------------------------
# _entity_quality
# ---------------------------------------------------------------------------

class TestEntityQuality:
    def test_ok_sources_gives_ok(self):
        entity = _entity("Alpha", sources=["src-1"])
        quality_map = {"src-1": "ok"}
        assert _entity_quality(entity, quality_map) == "ok"

    def test_warning_source_gives_warning(self):
        entity = _entity("Alpha", sources=["src-1"])
        quality_map = {"src-1": "warning"}
        assert _entity_quality(entity, quality_map) == "warning"

    def test_low_source_gives_low(self):
        entity = _entity("Alpha", sources=["src-1"])
        quality_map = {"src-1": "low"}
        assert _entity_quality(entity, quality_map) == "low"

    def test_worst_source_wins(self):
        entity = _entity("Alpha", sources=["src-1", "src-2"])
        quality_map = {"src-1": "ok", "src-2": "low"}
        assert _entity_quality(entity, quality_map) == "low"

    def test_missing_source_defaults_to_ok(self):
        entity = _entity("Alpha", sources=["unknown-src"])
        assert _entity_quality(entity, {}) == "ok"


# ---------------------------------------------------------------------------
# _overall_entity_quality
# ---------------------------------------------------------------------------

class TestOverallEntityQuality:
    def test_all_clean_is_ok(self):
        entities = [_entity("A"), _entity("B")]
        quality_map = {"src-1": "ok"}
        assert _overall_entity_quality(entities, 0, quality_map) == "ok"

    def test_more_than_25pct_filtered_is_low(self):
        entities = [_entity("A"), _entity("B"), _entity("C")]
        quality_map = {"src-1": "ok"}
        assert _overall_entity_quality(entities, 2, quality_map) == "low"

    def test_between_5_and_25pct_is_warning(self):
        # 1 filtered out of 10 total = 10%
        entities = [_entity("A")] * 9
        quality_map = {"src-1": "ok"}
        assert _overall_entity_quality(entities, 1, quality_map) == "warning"

    def test_flagged_entities_count_toward_ratio(self):
        # 1 low-quality entity out of 4 total = 25% -> boundary
        entities = [_entity("A", ["src-bad"]), _entity("B"), _entity("C"), _entity("D")]
        quality_map = {"src-bad": "low", "src-1": "ok"}
        result = _overall_entity_quality(entities, 0, quality_map)
        assert result in ("warning", "low")

    def test_empty_returns_ok(self):
        assert _overall_entity_quality([], 0, {}) == "ok"


# ---------------------------------------------------------------------------
# _build_overall_quality
# ---------------------------------------------------------------------------

class TestBuildOverallQuality:
    def test_zero_warnings_is_ok(self):
        eq = {"total": 10, "sources_with_warnings": 0}
        assert _build_overall_quality(eq) == "ok"

    def test_some_warnings_is_warning(self):
        eq = {"total": 10, "sources_with_warnings": 2}
        assert _build_overall_quality(eq) == "warning"

    def test_more_than_25pct_is_low(self):
        eq = {"total": 10, "sources_with_warnings": 4}
        assert _build_overall_quality(eq) == "low"

    def test_empty_is_ok(self):
        eq = {"total": 0, "sources_with_warnings": 0}
        assert _build_overall_quality(eq) == "ok"


# ---------------------------------------------------------------------------
# write_build_report
# ---------------------------------------------------------------------------

class TestWriteBuildReport:
    def test_creates_file(self, tmp_path):
        (tmp_path / "kb").mkdir()
        eq = {"total": 5, "sources_with_warnings": 0}
        write_build_report(tmp_path, eq, "ok")
        report_path = tmp_path / "kb" / "build-report.json"
        assert report_path.exists()

    def test_ok_quality_no_recommendation_action(self, tmp_path):
        (tmp_path / "kb").mkdir()
        eq = {"total": 5, "sources_with_warnings": 0}
        write_build_report(tmp_path, eq, "ok")
        report = json.loads((tmp_path / "kb" / "build-report.json").read_text())
        assert report["overall_quality"] == "ok"
        assert "No action" in report["recommendation"]

    def test_warning_quality_has_recommendation(self, tmp_path):
        (tmp_path / "kb").mkdir()
        eq = {"total": 5, "sources_with_warnings": 2}
        write_build_report(tmp_path, eq, "warning")
        report = json.loads((tmp_path / "kb" / "build-report.json").read_text())
        assert report["overall_quality"] == "warning"
        assert report["sources_with_warnings"] == 2
        assert "Re-extract" in report["recommendation"]

    def test_report_includes_build_date(self, tmp_path):
        (tmp_path / "kb").mkdir()
        eq = {"total": 3, "sources_with_warnings": 0}
        write_build_report(tmp_path, eq, "ok")
        report = json.loads((tmp_path / "kb" / "build-report.json").read_text())
        assert "build_date" in report
        assert "Z" in report["build_date"]


# ---------------------------------------------------------------------------
# write_index_yaml — quality block and per-entity quality
# ---------------------------------------------------------------------------

def _setup_project(tmp_path: Path) -> Path:
    (tmp_path / ".knowledge-project").write_text("{}")
    (tmp_path / "kb").mkdir()
    (tmp_path / "kb" / "questions").mkdir()
    return tmp_path


def _make_ext(source_id: str, flags: list[str] | None = None) -> dict:
    return {
        "source_id": source_id,
        "schema_version": "1",
        "entities": [],
        "key_facts": [],
        "quality": {"flags": flags or [], "warnings": [], "text_coverage": None},
        "summary": {"short": "s", "long": "l"},
    }


class TestIndexYamlQualityBlock:
    def _read_yaml_raw(self, path: Path) -> str:
        return (path / "kb" / "index.yaml").read_text()

    def test_quality_block_present(self, tmp_path):
        root = _setup_project(tmp_path)
        exts = [_make_ext("src-1")]
        entities = [_entity("Alpha")]
        qmap = {"src-1": "ok"}
        write_index_yaml(root, entities, exts, [], [], quality_map=qmap, filtered_count=0, broken_wikilink_count=0)
        text = self._read_yaml_raw(tmp_path)
        assert "entity_quality:" in text
        assert "broken_wikilinks:" in text
        assert "skipped_low_confidence_entities:" in text
        assert "glossary_stubs:" in text

    def test_clean_build_gives_ok_entity_quality(self, tmp_path):
        root = _setup_project(tmp_path)
        exts = [_make_ext("src-1")]
        entities = [_entity("Alpha")]
        qmap = {"src-1": "ok"}
        write_index_yaml(root, entities, exts, [], [], quality_map=qmap, filtered_count=0, broken_wikilink_count=0)
        text = self._read_yaml_raw(tmp_path)
        assert 'entity_quality: "ok"' in text

    def test_noisy_build_gives_low_entity_quality(self, tmp_path):
        root = _setup_project(tmp_path)
        exts = [_make_ext("src-1")]
        # 3 promoted entities, all flagged; 1 filtered = 4/4 = 100% > 25%
        entities = [_entity("A", ["src-bad"]), _entity("B", ["src-bad"]), _entity("C", ["src-bad"])]
        qmap = {"src-bad": "low"}
        write_index_yaml(root, entities, exts, [], [], quality_map=qmap, filtered_count=1, broken_wikilink_count=0)
        text = self._read_yaml_raw(tmp_path)
        assert 'entity_quality: "low"' in text

    def test_per_entity_quality_field_present(self, tmp_path):
        root = _setup_project(tmp_path)
        exts = [_make_ext("src-1")]
        entities = [_entity("Alpha")]
        qmap = {"src-1": "ok"}
        write_index_yaml(root, entities, exts, [], [], quality_map=qmap, filtered_count=0, broken_wikilink_count=0)
        text = self._read_yaml_raw(tmp_path)
        assert 'quality: "ok"' in text

    def test_broken_wikilink_count_in_quality_block(self, tmp_path):
        root = _setup_project(tmp_path)
        exts = [_make_ext("src-1")]
        entities = [_entity("Alpha")]
        write_index_yaml(root, entities, exts, [], [], broken_wikilink_count=7)
        text = self._read_yaml_raw(tmp_path)
        assert "broken_wikilinks: 7" in text

    def test_glossary_stubs_count_in_quality_block(self, tmp_path):
        root = _setup_project(tmp_path)
        exts = [_make_ext("src-1")]
        entities = [_entity("Alpha")]
        write_index_yaml(root, entities, exts, [], stubs=["Alpha", "Beta"], broken_wikilink_count=0)
        text = self._read_yaml_raw(tmp_path)
        assert "glossary_stubs: 2" in text

    def test_no_quality_map_defaults_to_ok(self, tmp_path):
        root = _setup_project(tmp_path)
        exts = [_make_ext("src-1")]
        entities = [_entity("Alpha")]
        write_index_yaml(root, entities, exts, [], [])
        text = self._read_yaml_raw(tmp_path)
        assert "entity_quality:" in text
