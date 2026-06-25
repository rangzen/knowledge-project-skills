"""Tests for _inject_wikilinks(), _build_slug_map(), and wikilink injection in write_entity_page()."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/kb/scripts/kb_build.py"
spec = importlib.util.spec_from_file_location("kb_build", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

_inject_wikilinks = _mod._inject_wikilinks
_build_slug_map = _mod._build_slug_map
write_entity_page = _mod.write_entity_page


def _entity(name, bodies=None, context="A short description.", aliases=None, slug=None):
    return {
        "name": name,
        "type": "concept",
        "context": context,
        "aliases": aliases or [],
        "_sources": [b["source"] for b in bodies] if bodies else ["src-1"],
        "_bodies": bodies or [],
        "_slug": slug or name.lower().replace(" ", "-"),
    }


class TestInjectWikilinks:
    def test_basic_name_linked(self):
        slug_map = {"cairn": ("cairn", "Cairn")}
        assert _inject_wikilinks("Cairn is a game.", slug_map, "other") == "[[cairn|Cairn]] is a game."

    def test_longest_name_matched_first(self):
        slug_map = {
            "into the odd": ("into-the-odd", "Into the Odd"),
            "odd": ("odd", "Odd"),
        }
        result = _inject_wikilinks("Creator of Into the Odd.", slug_map, "chris")
        assert "[[into-the-odd|Into the Odd]]" in result
        assert "[[odd|Odd]]" not in result

    def test_first_occurrence_only_linked(self):
        slug_map = {"cairn": ("cairn", "Cairn")}
        result = _inject_wikilinks("Cairn is good. Cairn is popular.", slug_map, "other")
        assert result.count("[[cairn|Cairn]]") == 1
        assert "Cairn is popular." in result

    def test_self_link_skipped(self):
        slug_map = {"cairn": ("cairn", "Cairn")}
        result = _inject_wikilinks("Cairn rules.", slug_map, "cairn")
        assert "[[" not in result

    def test_existing_wikilink_not_double_linked(self):
        slug_map = {"cairn": ("cairn", "Cairn")}
        result = _inject_wikilinks("See [[cairn|Cairn]] for more.", slug_map, "other")
        assert result == "See [[cairn|Cairn]] for more."

    def test_word_boundary_no_partial_match(self):
        slug_map = {"cairn": ("cairn", "Cairn")}
        result = _inject_wikilinks("The Cairns are rocky.", slug_map, "other")
        assert "[[cairn|Cairn]]" not in result

    def test_case_insensitive_match_uses_display_name(self):
        slug_map = {"into the odd": ("into-the-odd", "Into the Odd")}
        result = _inject_wikilinks("into the odd inspired many.", slug_map, "other")
        assert "[[into-the-odd|Into the Odd]]" in result

    def test_empty_slug_map(self):
        assert _inject_wikilinks("Some text.", {}, "other") == "Some text."

    def test_empty_text(self):
        slug_map = {"cairn": ("cairn", "Cairn")}
        assert _inject_wikilinks("", slug_map, "other") == ""

    def test_multiple_names_all_linked(self):
        slug_map = {
            "into the odd": ("into-the-odd", "Into the Odd"),
            "cairn": ("cairn", "Cairn"),
        }
        result = _inject_wikilinks("Into the Odd and Cairn are related.", slug_map, "other")
        assert "[[into-the-odd|Into the Odd]]" in result
        assert "[[cairn|Cairn]]" in result

    def test_name_inside_existing_wikilink_label_not_double_linked(self):
        # "Cairn" appears as the label in an existing [[...|Cairn]] — must not be re-linked
        slug_map = {"cairn": ("cairn", "Cairn")}
        result = _inject_wikilinks("See [[cairn-2e|Cairn]] second edition.", slug_map, "other")
        assert result.count("[[") == 1


class TestBuildSlugMap:
    def test_entity_name_added(self):
        entities = [{"name": "Cairn", "type": "product", "_slug": "cairn", "aliases": []}]
        slug_map = _build_slug_map(entities)
        assert slug_map["cairn"] == ("cairn", "Cairn")

    def test_alias_added_to_same_slug(self):
        entities = [{"name": "Cairn", "type": "product", "_slug": "cairn", "aliases": ["Cairn RPG"]}]
        slug_map = _build_slug_map(entities)
        assert "cairn rpg" in slug_map
        assert slug_map["cairn rpg"] == ("cairn", "Cairn RPG")

    def test_multiple_entities(self):
        entities = [
            {"name": "Cairn", "type": "product", "_slug": "cairn", "aliases": []},
            {"name": "Into the Odd", "type": "product", "_slug": "into-the-odd", "aliases": []},
        ]
        slug_map = _build_slug_map(entities)
        assert "cairn" in slug_map
        assert "into the odd" in slug_map

    def test_entity_without_aliases_key(self):
        entities = [{"name": "Cairn", "type": "product", "_slug": "cairn"}]
        slug_map = _build_slug_map(entities)
        assert "cairn" in slug_map


class TestWriteEntityPageWikilinks:
    def test_context_gets_wikilinks(self, tmp_path):
        slug_map = {
            "into the odd": ("into-the-odd", "Into the Odd"),
            "cairn": ("cairn", "Cairn"),
        }
        entity = _entity("Chris", context="Creator of Into the Odd and Cairn.")
        write_entity_page(tmp_path, entity, "build", slug_map)
        text = (tmp_path / "kb" / "concepts" / "chris.md").read_text()
        assert "[[into-the-odd|Into the Odd]]" in text
        assert "[[cairn|Cairn]]" in text

    def test_single_body_gets_wikilinks(self, tmp_path):
        slug_map = {"cairn": ("cairn", "Cairn")}
        entity = _entity("Chris", bodies=[{"source": "src-1", "body": "See Cairn for details."}])
        write_entity_page(tmp_path, entity, "build", slug_map)
        text = (tmp_path / "kb" / "concepts" / "chris.md").read_text()
        assert "[[cairn|Cairn]]" in text

    def test_multiple_bodies_each_get_wikilinks(self, tmp_path):
        slug_map = {"cairn": ("cairn", "Cairn"), "knave": ("knave", "Knave")}
        entity = _entity("Chris", bodies=[
            {"source": "src-1", "body": "Made Cairn."},
            {"source": "src-2", "body": "Also made Knave."},
        ])
        write_entity_page(tmp_path, entity, "build", slug_map)
        text = (tmp_path / "kb" / "concepts" / "chris.md").read_text()
        assert "[[cairn|Cairn]]" in text
        assert "[[knave|Knave]]" in text

    def test_no_self_link_in_page(self, tmp_path):
        slug_map = {
            "chris": ("chris", "Chris"),
            "cairn": ("cairn", "Cairn"),
        }
        entity = _entity("Chris", context="Chris created Cairn.", slug="chris")
        write_entity_page(tmp_path, entity, "build", slug_map)
        text = (tmp_path / "kb" / "concepts" / "chris.md").read_text()
        assert "[[chris|Chris]]" not in text
        assert "[[cairn|Cairn]]" in text

    def test_no_slug_map_preserves_plain_text(self, tmp_path):
        entity = _entity("Chris", context="Creator of Cairn.")
        write_entity_page(tmp_path, entity, "build")
        text = (tmp_path / "kb" / "concepts" / "chris.md").read_text()
        assert "[[" not in text
