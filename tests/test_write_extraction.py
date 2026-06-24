"""Tests for write_extraction.py: quality guardrails and extraction status."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/extract/scripts/write_extraction.py"
spec = importlib.util.spec_from_file_location("write_extraction", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

quality_check = _mod.quality_check
quality_level = _mod.quality_level
deduplicate_entities = _mod.deduplicate_entities


VALID_ENTITY = {"name": "Acme Corp", "type": "organization", "aliases": [], "context": "subject", "source_ref": "src"}


def _extraction(summary_short="A detailed one-sentence summary of this document content.", entities=None, facts=None):
    return {
        "schema_version": "1",
        "source_id": "src-001",
        "source_ref": "sources/src-001/file.pdf",
        "extracted_at": "2026-06-24T10:00:00Z",
        "model": "claude-sonnet-4-6",
        "summary": {"short": summary_short, "long": "Long summary goes here with more detail about the content."},
        "entities": entities if entities is not None else [VALID_ENTITY, {"name": "Alice", "type": "person", "aliases": [], "context": "author", "source_ref": "src"}],
        "key_facts": facts if facts is not None else [{"fact": "Key finding.", "source_ref": "src", "page": 1}],
        "dates": [],
        "schema": None,
        "images": [],
    }


class TestQualityCheck:
    def test_ok_extraction(self):
        q = quality_check(_extraction())
        assert q["flags"] == []
        assert q["warnings"] == []
        assert quality_level(q) == "ok"

    def test_no_text_when_empty(self):
        data = _extraction(summary_short="Short.", entities=[], facts=[])
        q = quality_check(data)
        assert "no_text" in q["flags"]
        assert quality_level(q) == "low"

    def test_low_entity_count_zero_entities(self):
        data = _extraction(entities=[])  # summary ok, just entities missing
        q = quality_check(data)
        assert "low_entity_count" in q["flags"]
        assert "low_summary" not in q["flags"]
        assert quality_level(q) == "warning"

    def test_low_entity_count_one_entity(self):
        data = _extraction(entities=[VALID_ENTITY])
        q = quality_check(data)
        assert "low_entity_count" in q["flags"]

    def test_low_summary_flag(self):
        data = _extraction(summary_short="Too short.")
        q = quality_check(data)
        assert "low_summary" in q["flags"]

    def test_two_flags_gives_low_quality(self):
        data = _extraction(summary_short="Short.", entities=[])
        q = quality_check(data)
        assert quality_level(q) == "low"

    def test_text_coverage_is_null(self):
        q = quality_check(_extraction())
        assert q["text_coverage"] is None


class TestDeduplicateEntities:
    def test_no_duplicates(self):
        entities = [
            {"name": "Alice", "type": "person"},
            {"name": "Bob", "type": "person"},
        ]
        result, removed = deduplicate_entities(entities)
        assert len(result) == 2
        assert removed == 0

    def test_exact_duplicate_removed(self):
        entities = [
            {"name": "Acme Corp", "type": "organization"},
            {"name": "Acme Corp", "type": "organization"},
        ]
        result, removed = deduplicate_entities(entities)
        assert len(result) == 1
        assert removed == 1

    def test_case_insensitive_dedup(self):
        entities = [
            {"name": "acme corp", "type": "organization"},
            {"name": "Acme Corp", "type": "organization"},
            {"name": "ACME CORP", "type": "organization"},
        ]
        result, removed = deduplicate_entities(entities)
        assert len(result) == 1
        assert removed == 2

    def test_first_occurrence_kept(self):
        entities = [
            {"name": "Alpha", "type": "concept", "context": "first"},
            {"name": "Alpha", "type": "concept", "context": "second"},
        ]
        result, _ = deduplicate_entities(entities)
        assert result[0]["context"] == "first"


class TestWriteExtractionIntegration:
    """End-to-end test: run write_extraction.py via subprocess in a temp project."""

    def test_quality_block_written_to_json(self, tmp_path):
        import subprocess
        (tmp_path / ".knowledge-project").write_text("{}")
        src_dir = tmp_path / "sources" / "src-001"
        src_dir.mkdir(parents=True)
        (src_dir / "file.pdf").write_bytes(b"%PDF fake")
        (src_dir / ".meta.json").write_text(json.dumps({
            "source_id": "src-001",
            "origin": str(src_dir / "file.pdf"),
            "type": "pdf",
            "ingested_at": "2026-06-24T10:00:00Z",
            "hash": "sha256:abc",
            "page_count": 1,
            "sensitive": False,
            "extraction": {"status": "pending"},
            "stale": False,
        }))
        (tmp_path / "extractions").mkdir()

        data = _extraction()
        result = subprocess.run(
            ["uv", "run", str(SCRIPT), "--source-id", "src-001"],
            input=json.dumps(data),
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, result.stderr

        out = json.loads((tmp_path / "extractions" / "src-001.json").read_text())
        assert "quality" in out
        assert isinstance(out["quality"]["flags"], list)
        assert isinstance(out["quality"]["warnings"], list)

        meta = json.loads((src_dir / ".meta.json").read_text())
        assert "extracted" not in meta
        assert meta["extraction"]["status"] == "complete"
        assert meta["extraction"]["quality"] in ("ok", "warning", "low")
        assert "extracted_at" in meta["extraction"]

    def test_zero_entities_written_not_dropped(self, tmp_path):
        import subprocess
        (tmp_path / ".knowledge-project").write_text("{}")
        src_dir = tmp_path / "sources" / "src-002"
        src_dir.mkdir(parents=True)
        (src_dir / "file.pdf").write_bytes(b"%PDF fake")
        (src_dir / ".meta.json").write_text(json.dumps({
            "source_id": "src-002",
            "origin": str(src_dir / "file.pdf"),
            "type": "pdf",
            "ingested_at": "2026-06-24T10:00:00Z",
            "hash": "sha256:abc",
            "page_count": 1,
            "sensitive": False,
            "extraction": {"status": "pending"},
            "stale": False,
        }))
        (tmp_path / "extractions").mkdir()

        data = _extraction(entities=[])
        result = subprocess.run(
            ["uv", "run", str(SCRIPT), "--source-id", "src-002"],
            input=json.dumps(data),
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "extractions" / "src-002.json").exists()
        out = json.loads((tmp_path / "extractions" / "src-002.json").read_text())
        assert "low_entity_count" in out["quality"]["flags"]
