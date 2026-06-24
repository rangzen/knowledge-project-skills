"""Tests for the extended resolve_entities() in kb_build.py."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/kb/scripts/kb_build.py"
spec = importlib.util.spec_from_file_location("kb_build", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

resolve_entities = _mod.resolve_entities


def _ext(source_id: str, entities: list[dict]) -> dict:
    return {"source_id": source_id, "entities": entities}


def _entity(name: str, etype: str = "concept", aliases: list[str] | None = None, confidence: float | None = None) -> dict:
    e = {"name": name, "type": etype, "aliases": aliases or [], "context": "test", "source_ref": "src"}
    if confidence is not None:
        e["confidence"] = confidence
    return e


class TestResolveEntitiesBasic:
    def test_single_entity(self):
        entities, conflicts = resolve_entities([_ext("s1", [_entity("Alpha")])])
        assert len(entities) == 1
        assert entities[0]["name"] == "Alpha"
        assert conflicts == []

    def test_same_name_same_type_merges_sources(self):
        entities, conflicts = resolve_entities([
            _ext("s1", [_entity("Alpha")]),
            _ext("s2", [_entity("Alpha")]),
        ])
        assert len(entities) == 1
        assert set(entities[0]["_sources"]) == {"s1", "s2"}
        assert conflicts == []

    def test_case_insensitive_merge(self):
        entities, conflicts = resolve_entities([
            _ext("s1", [_entity("Alpha")]),
            _ext("s2", [_entity("ALPHA")]),
        ])
        assert len(entities) == 1
        assert conflicts == []


class TestTypeConflicts:
    def test_same_name_different_type_logs_conflict(self):
        entities, conflicts = resolve_entities([
            _ext("s1", [_entity("MyCenter", etype="product")]),
            _ext("s2", [_entity("mycenter", etype="concept")]),
        ])
        assert len(conflicts) == 1
        assert conflicts[0]["name"] == "mycenter"
        assert conflicts[0]["existing_type"] == "product"
        assert conflicts[0]["new_type"] == "concept"

    def test_type_conflict_keeps_first_seen(self):
        entities, conflicts = resolve_entities([
            _ext("s1", [_entity("MyCenter", etype="product")]),
            _ext("s2", [_entity("mycenter", etype="concept")]),
        ])
        assert len(entities) == 1
        assert entities[0]["type"] == "product"

    def test_no_conflict_for_same_type(self):
        entities, conflicts = resolve_entities([
            _ext("s1", [_entity("Alpha", etype="concept")]),
            _ext("s2", [_entity("Alpha", etype="concept")]),
        ])
        assert conflicts == []


class TestAliasMerge:
    def test_entity_b_absorbed_when_a_has_b_as_alias(self):
        entities, conflicts = resolve_entities([
            _ext("s1", [_entity("Alpha", etype="product", aliases=["Beta"])]),
            _ext("s2", [_entity("Beta", etype="product")]),
        ])
        assert len(entities) == 1
        assert entities[0]["name"] == "Alpha"
        assert "Beta" in entities[0]["aliases"]
        assert "s2" in entities[0]["_sources"]
        assert conflicts == []

    def test_alias_merge_preserves_existing_aliases(self):
        entities, conflicts = resolve_entities([
            _ext("s1", [_entity("Alpha", etype="product", aliases=["Beta", "Gamma"])]),
            _ext("s2", [_entity("Beta", etype="product")]),
        ])
        assert len(entities) == 1
        assert "Gamma" in entities[0]["aliases"]

    def test_no_alias_merge_when_no_match(self):
        entities, conflicts = resolve_entities([
            _ext("s1", [_entity("Alpha", etype="product", aliases=["Delta"])]),
            _ext("s2", [_entity("Beta", etype="product")]),
        ])
        assert len(entities) == 2

    def test_alias_merge_order_independent(self):
        # B appears BEFORE A in the extraction stream; A has B as alias.
        entities, conflicts = resolve_entities([
            _ext("s1", [_entity("Beta", etype="product")]),
            _ext("s2", [_entity("Alpha", etype="product", aliases=["Beta"])]),
        ])
        assert len(entities) == 1
        assert entities[0]["name"] == "Alpha"
        assert "Beta" in entities[0]["aliases"]


class TestConfidenceThreshold:
    def test_entity_below_threshold_excluded(self):
        entities, _ = resolve_entities(
            [_ext("s1", [_entity("Alpha", confidence=0.3)])],
            confidence_threshold=0.5,
        )
        assert len(entities) == 0

    def test_entity_at_threshold_included(self):
        entities, _ = resolve_entities(
            [_ext("s1", [_entity("Alpha", confidence=0.5)])],
            confidence_threshold=0.5,
        )
        assert len(entities) == 1

    def test_entity_above_threshold_included(self):
        entities, _ = resolve_entities(
            [_ext("s1", [_entity("Alpha", confidence=0.9)])],
            confidence_threshold=0.5,
        )
        assert len(entities) == 1

    def test_zero_threshold_includes_all(self):
        entities, _ = resolve_entities(
            [_ext("s1", [_entity("Alpha", confidence=0.0)])],
            confidence_threshold=0.0,
        )
        assert len(entities) == 1

    def test_entity_without_confidence_field_included(self):
        entities, _ = resolve_entities(
            [_ext("s1", [_entity("Alpha")])],
            confidence_threshold=0.5,
        )
        assert len(entities) == 1


def _entity_with_body(name: str, body: str, etype: str = "concept") -> dict:
    e = _entity(name, etype)
    e["body"] = body
    return e


class TestBodyCollection:
    def test_entity_with_body_collects_one_entry(self):
        entities, _ = resolve_entities([_ext("s1", [_entity_with_body("Combat", "## Rules\nFight.")])])
        assert len(entities[0]["_bodies"]) == 1
        assert entities[0]["_bodies"][0]["source"] == "s1"
        assert "Fight." in entities[0]["_bodies"][0]["body"]

    def test_entity_without_body_has_empty_bodies(self):
        entities, _ = resolve_entities([_ext("s1", [_entity("Alpha")])])
        assert entities[0]["_bodies"] == []

    def test_same_entity_two_sources_both_with_body(self):
        entities, _ = resolve_entities([
            _ext("s1", [_entity_with_body("Combat", "Body from s1.")]),
            _ext("s2", [_entity_with_body("Combat", "Body from s2.")]),
        ])
        assert len(entities) == 1
        assert len(entities[0]["_bodies"]) == 2
        sources = {b["source"] for b in entities[0]["_bodies"]}
        assert sources == {"s1", "s2"}

    def test_same_entity_only_first_source_has_body(self):
        entities, _ = resolve_entities([
            _ext("s1", [_entity_with_body("Combat", "Body from s1.")]),
            _ext("s2", [_entity("Combat")]),
        ])
        assert len(entities) == 1
        assert len(entities[0]["_bodies"]) == 1
        assert entities[0]["_bodies"][0]["source"] == "s1"

    def test_same_entity_only_second_source_has_body(self):
        entities, _ = resolve_entities([
            _ext("s1", [_entity("Combat")]),
            _ext("s2", [_entity_with_body("Combat", "Body from s2.")]),
        ])
        assert len(entities) == 1
        assert len(entities[0]["_bodies"]) == 1
        assert entities[0]["_bodies"][0]["source"] == "s2"
