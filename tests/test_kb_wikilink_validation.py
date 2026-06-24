"""Tests for validate_wikilinks() in kb_build.py."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/kb/scripts/kb_build.py"
spec = importlib.util.spec_from_file_location("kb_build", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

_wikilink_target = _mod._wikilink_target
validate_wikilinks = _mod.validate_wikilinks


class TestWikilinkTargetParsing:
    def test_plain_link(self):
        assert _wikilink_target("target") == "target"

    def test_alias_link(self):
        assert _wikilink_target("target|label") == "target"

    def test_alias_with_spaces(self):
        assert _wikilink_target("target|label with spaces") == "target"

    def test_anchor_stripped(self):
        assert _wikilink_target("Glossary#Section") == "Glossary"

    def test_slugified_target_with_punctuation_alias(self):
        assert _wikilink_target("a-d|A&D") == "a-d"


class TestValidateWikilinks:
    def _make_kb(self, tmp_path: Path, pages: dict[str, str]) -> Path:
        kb = tmp_path / "kb"
        kb.mkdir()
        for name, content in pages.items():
            (kb / name).write_text(content)
        (tmp_path / ".knowledge-project").write_text("{}")
        return tmp_path

    def test_plain_link_resolves(self, tmp_path):
        root = self._make_kb(tmp_path, {
            "alpha.md": "See [[alpha]].",
        })
        broken = validate_wikilinks(root)
        assert broken == []

    def test_alias_link_resolves(self, tmp_path):
        root = self._make_kb(tmp_path, {
            "alpha.md": "See [[alpha|Alpha Page]].",
        })
        broken = validate_wikilinks(root)
        assert broken == []

    def test_alias_label_not_validated_as_target(self, tmp_path):
        # Page "alpha.md" exists; link uses alias "Alpha Page" which does NOT have a page.
        # The validator must resolve against "alpha", not "Alpha Page".
        root = self._make_kb(tmp_path, {
            "alpha.md": "See [[alpha|Alpha Page]].",
        })
        broken = validate_wikilinks(root)
        assert broken == []

    def test_anchor_link_resolves(self, tmp_path):
        root = self._make_kb(tmp_path, {
            "glossary.md": "See [[glossary#Terms]].",
        })
        broken = validate_wikilinks(root)
        assert broken == []

    def test_slugified_alias_resolves(self, tmp_path):
        # "a-d.md" exists; link is [[a-d|A&D]]
        root = self._make_kb(tmp_path, {
            "a-d.md": "Article.",
            "other.md": "See [[a-d|A&D]].",
        })
        broken = validate_wikilinks(root)
        assert broken == []

    def test_genuinely_broken_link_reported(self, tmp_path):
        root = self._make_kb(tmp_path, {
            "alpha.md": "See [[does-not-exist]].",
        })
        broken = validate_wikilinks(root)
        assert len(broken) == 1
        assert broken[0][1] == "does-not-exist"

    def test_broken_alias_link_target_reported(self, tmp_path):
        # Target "missing" doesn't exist; alias "Nice Name" should not confuse validator.
        root = self._make_kb(tmp_path, {
            "alpha.md": "See [[missing|Nice Name]].",
        })
        broken = validate_wikilinks(root)
        assert len(broken) == 1
        assert broken[0][1] == "missing|Nice Name"
