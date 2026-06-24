"""Tests for _glossary_definition() and glossary stub tracking in kb_build.py."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/kb/scripts/kb_build.py"
spec = importlib.util.spec_from_file_location("kb_build", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

_glossary_definition = _mod._glossary_definition
_STUB_TEXT = _mod._STUB_TEXT


def _entity(name: str, context: str = "", summary: str = "", etype: str = "concept") -> dict:
    e = {"name": name, "type": etype, "context": context, "_sources": ["src-1"]}
    if summary:
        e["summary"] = summary
    return e


def _fact(text: str) -> dict:
    return {"fact": text}


class TestGlossaryDefinitionContext:
    def test_adequate_context_used_directly(self):
        entity = _entity("Alpha", context="Alpha is a well-known framework for building things.")
        text, is_stub = _glossary_definition(entity, [])
        assert text == "Alpha is a well-known framework for building things."
        assert not is_stub

    def test_short_context_becomes_stub(self):
        entity = _entity("Beta", context="Short.")
        text, is_stub = _glossary_definition(entity, [])
        assert text == _STUB_TEXT
        assert is_stub

    def test_heading_context_is_not_usable(self):
        entity = _entity("Gamma", context="# Getting Started")
        text, is_stub = _glossary_definition(entity, [])
        assert text == _STUB_TEXT
        assert is_stub

    def test_empty_context_is_stub(self):
        entity = _entity("Delta", context="")
        text, is_stub = _glossary_definition(entity, [])
        assert is_stub

    def test_context_exactly_30_chars_is_usable(self):
        context = "x" * 30
        entity = _entity("Epsilon", context=context)
        text, is_stub = _glossary_definition(entity, [])
        assert text == context
        assert not is_stub

    def test_context_29_chars_is_stub(self):
        entity = _entity("Zeta", context="x" * 29)
        _, is_stub = _glossary_definition(entity, [])
        assert is_stub


class TestGlossaryDefinitionSummaryFallback:
    def test_summary_preferred_when_longer_than_context(self):
        entity = _entity(
            "Mu",
            context="Short ctx.",
            summary="Mu is a comprehensive module that handles data ingestion pipelines.",
        )
        text, is_stub = _glossary_definition(entity, [])
        assert text == "Mu is a comprehensive module that handles data ingestion pipelines."
        assert not is_stub

    def test_context_kept_when_longer_than_summary(self):
        ctx = "Mu is a comprehensive module that handles data ingestion pipelines."
        entity = _entity("Mu", context=ctx, summary="Short summary.")
        text, is_stub = _glossary_definition(entity, [])
        assert text == ctx
        assert not is_stub

    def test_summary_used_when_context_is_heading(self):
        entity = _entity(
            "Nu",
            context="# Introduction",
            summary="Nu is a standard library for numerical computation in Python.",
        )
        text, is_stub = _glossary_definition(entity, [])
        assert text == "Nu is a standard library for numerical computation in Python."
        assert not is_stub

    def test_short_summary_and_short_context_falls_through_to_stub(self):
        entity = _entity("Xi", context="Tiny.", summary="Also tiny.")
        _, is_stub = _glossary_definition(entity, [])
        assert is_stub


class TestGlossaryDefinitionFactFallback:
    def test_matching_fact_used_when_context_is_heading(self):
        entity = _entity("Omicron", context="# Omicron")
        facts = [_fact("Omicron adoption rate increased by 40% year-over-year across all regions.")]
        text, is_stub = _glossary_definition(entity, facts)
        assert "Omicron adoption rate" in text
        assert not is_stub

    def test_matching_fact_used_when_context_is_short(self):
        entity = _entity("Pi", context="See above.")
        facts = [_fact("Pi is a mathematical constant representing the ratio of a circle's circumference.")]
        text, is_stub = _glossary_definition(entity, facts)
        assert "mathematical constant" in text
        assert not is_stub

    def test_non_matching_fact_ignored(self):
        entity = _entity("Rho", context="Short.")
        facts = [_fact("Sigma is an entirely different entity with its own long description here.")]
        _, is_stub = _glossary_definition(entity, facts)
        assert is_stub

    def test_short_fact_under_30_chars_skipped(self):
        entity = _entity("Tau", context="Short.")
        facts = [_fact("Tau: small.")]
        _, is_stub = _glossary_definition(entity, facts)
        assert is_stub

    def test_fact_match_is_case_insensitive(self):
        entity = _entity("Upsilon", context="# Upsilon")
        facts = [_fact("UPSILON is a protocol used in distributed systems for consensus.")]
        text, is_stub = _glossary_definition(entity, facts)
        assert not is_stub

    def test_first_matching_fact_wins(self):
        entity = _entity("Phi", context="Short.")
        facts = [
            _fact("Phi is the golden ratio used in design and architecture worldwide."),
            _fact("Phi also appears in Fibonacci sequences and many natural phenomena."),
        ]
        text, is_stub = _glossary_definition(entity, facts)
        assert "golden ratio" in text
        assert not is_stub
