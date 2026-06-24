"""Tests for write_entity_page() body rendering in kb_build.py."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/kb/scripts/kb_build.py"
spec = importlib.util.spec_from_file_location("kb_build", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

write_entity_page = _mod.write_entity_page


def _entity(name: str, bodies: list[dict] | None = None, context: str = "A short description.") -> dict:
    return {
        "name": name,
        "type": "concept",
        "context": context,
        "aliases": [],
        "_sources": [b["source"] for b in bodies] if bodies else ["src-1"],
        "_bodies": bodies if bodies is not None else [],
        "_slug": name.lower(),
    }


class TestNoBody:
    def test_context_written_as_lead_paragraph(self, tmp_path):
        entity = _entity("Alpha", context="Alpha is a test entity.")
        write_entity_page(tmp_path, entity, "build")
        text = (tmp_path / "kb" / "concepts" / "alpha.md").read_text()
        assert "Alpha is a test entity." in text

    def test_no_body_content_beyond_context(self, tmp_path):
        entity = _entity("Alpha", context="Short description.")
        write_entity_page(tmp_path, entity, "build")
        text = (tmp_path / "kb" / "concepts" / "alpha.md").read_text()
        assert "### From" not in text


class TestSingleBody:
    def test_body_content_appears_after_context(self, tmp_path):
        body = "## Rules\n\nAttackers roll damage."
        entity = _entity("Combat", bodies=[{"source": "src-1", "body": body}])
        write_entity_page(tmp_path, entity, "build")
        text = (tmp_path / "kb" / "concepts" / "combat.md").read_text()
        assert "## Rules" in text
        assert "Attackers roll damage." in text

    def test_context_comes_before_body(self, tmp_path):
        body = "## Rules\n\nSome rule."
        entity = _entity("Combat", bodies=[{"source": "src-1", "body": body}], context="The combat system.")
        write_entity_page(tmp_path, entity, "build")
        text = (tmp_path / "kb" / "concepts" / "combat.md").read_text()
        assert text.index("The combat system.") < text.index("## Rules")

    def test_no_source_attribution_header_for_single_body(self, tmp_path):
        body = "## Rules\n\nSome rule."
        entity = _entity("Combat", bodies=[{"source": "src-1", "body": body}])
        write_entity_page(tmp_path, entity, "build")
        text = (tmp_path / "kb" / "concepts" / "combat.md").read_text()
        assert "### From" not in text


class TestMultipleBodies:
    def test_each_body_has_source_header(self, tmp_path):
        entity = _entity("Combat", bodies=[
            {"source": "src-1", "body": "Body one."},
            {"source": "src-2", "body": "Body two."},
        ])
        write_entity_page(tmp_path, entity, "build")
        text = (tmp_path / "kb" / "concepts" / "combat.md").read_text()
        assert "### From src-1" in text
        assert "### From src-2" in text

    def test_both_body_contents_present(self, tmp_path):
        entity = _entity("Combat", bodies=[
            {"source": "src-1", "body": "Body one."},
            {"source": "src-2", "body": "Body two."},
        ])
        write_entity_page(tmp_path, entity, "build")
        text = (tmp_path / "kb" / "concepts" / "combat.md").read_text()
        assert "Body one." in text
        assert "Body two." in text

    def test_context_comes_before_source_headers(self, tmp_path):
        entity = _entity("Combat", bodies=[
            {"source": "src-1", "body": "Body one."},
            {"source": "src-2", "body": "Body two."},
        ], context="The combat system.")
        write_entity_page(tmp_path, entity, "build")
        text = (tmp_path / "kb" / "concepts" / "combat.md").read_text()
        assert text.index("The combat system.") < text.index("### From src-1")
