"""Tests for resolve_slugs() in kb_build.py — link generation consistency."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/kb/scripts/kb_build.py"
spec = importlib.util.spec_from_file_location("kb_build", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

resolve_slugs = _mod.resolve_slugs
slugify = _mod.slugify


def _entity(name: str, etype: str = "concept") -> dict:
    return {"name": name, "type": etype, "context": "test", "_sources": ["src-1"]}


class TestResolveSlugsNoCollision:
    def test_sets_slug_on_each_entity(self):
        entities = [_entity("Widget", "concept"), _entity("Gadget", "product")]
        resolve_slugs(entities)
        assert entities[0]["_slug"] == "widget"
        assert entities[1]["_slug"] == "gadget"

    def test_slug_matches_slugify_output(self):
        entities = [_entity("Large Language Model", "concept")]
        resolve_slugs(entities)
        assert entities[0]["_slug"] == slugify("Large Language Model")

    def test_returns_empty_list_when_no_collisions(self):
        entities = [_entity("Alpha"), _entity("Beta")]
        collisions = resolve_slugs(entities)
        assert collisions == []

    def test_single_entity(self):
        entities = [_entity("Solo")]
        resolve_slugs(entities)
        assert entities[0]["_slug"] == "solo"


class TestResolveSlugsCollision:
    def test_collision_appends_type_suffix(self):
        entities = [_entity("Widget", "product"), _entity("Widget", "concept")]
        resolve_slugs(entities)
        slugs = {e["_slug"] for e in entities}
        assert slugs == {"widget-product", "widget-concept"}

    def test_collision_returns_entry(self):
        entities = [_entity("Widget", "product"), _entity("Widget", "concept")]
        collisions = resolve_slugs(entities)
        assert len(collisions) == 1
        base_slug, types = collisions[0]
        assert base_slug == "widget"
        assert set(types) == {"product", "concept"}

    def test_non_colliding_entity_unaffected(self):
        entities = [
            _entity("Widget", "product"),
            _entity("Widget", "concept"),
            _entity("Gadget", "event"),
        ]
        resolve_slugs(entities)
        gadget = next(e for e in entities if e["name"] == "Gadget")
        assert gadget["_slug"] == "gadget"

    def test_three_way_collision_all_disambiguated(self):
        entities = [
            _entity("Foo", "concept"),
            _entity("Foo", "product"),
            _entity("Foo", "person"),
        ]
        collisions = resolve_slugs(entities)
        slugs = {e["_slug"] for e in entities}
        assert slugs == {"foo-concept", "foo-product", "foo-person"}
        assert len(collisions) == 1
