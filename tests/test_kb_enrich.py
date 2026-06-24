"""Tests for the enrich mode helpers in kb_build.py."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills/kb/scripts/kb_build.py"
spec = importlib.util.spec_from_file_location("kb_build", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

_page_has_body = _mod._page_has_body
_page_sources = _mod._page_sources
_clear_enrichment_flag = _mod._clear_enrichment_flag
run_enrich = _mod.run_enrich


_FRONTMATTER = "---\ntitle: Combat\nentity_type: concept\ngenerated: true\nsources:\n  - src-1\nlast_built: 2026-06-24\n---\n\n"


class TestPageHasBody:
    def test_missing_file_returns_false(self, tmp_path):
        assert _page_has_body(tmp_path / "nonexistent.md") is False

    def test_thin_page_returns_false(self, tmp_path):
        page = tmp_path / "combat.md"
        page.write_text(_FRONTMATTER + "# Combat\n\nThe combat system.\n\n**Type:** concept\n")
        assert _page_has_body(page) is False

    def test_page_with_h2_header_returns_true(self, tmp_path):
        page = tmp_path / "combat.md"
        page.write_text(_FRONTMATTER + "# Combat\n\nThe combat system.\n\n## Attacking\n\nRoll damage.\n")
        assert _page_has_body(page) is True

    def test_page_with_h3_header_returns_true(self, tmp_path):
        page = tmp_path / "combat.md"
        page.write_text(_FRONTMATTER + "# Combat\n\nLead.\n\n### Sub-rule\n\nDetails.\n")
        assert _page_has_body(page) is True

    def test_h1_title_only_does_not_count(self, tmp_path):
        page = tmp_path / "combat.md"
        page.write_text(_FRONTMATTER + "# Combat\n\nJust a one-liner.\n")
        assert _page_has_body(page) is False


class TestPageSources:
    def test_extracts_single_source(self, tmp_path):
        page = tmp_path / "combat.md"
        page.write_text(_FRONTMATTER + "# Combat\n")
        assert _page_sources(page) == ["src-1"]

    def test_extracts_multiple_sources(self, tmp_path):
        fm = "---\ntitle: Combat\nsources:\n  - src-1\n  - src-2\nlast_built: 2026-06-24\n---\n\n"
        page = tmp_path / "combat.md"
        page.write_text(fm + "# Combat\n")
        assert _page_sources(page) == ["src-1", "src-2"]

    def test_no_frontmatter_returns_empty(self, tmp_path):
        page = tmp_path / "combat.md"
        page.write_text("# Combat\n\nNo frontmatter here.\n")
        assert _page_sources(page) == []


class TestClearEnrichmentFlag:
    def _make_question(self, tmp_path, target: str | None = "concepts/combat") -> Path:
        target_line = f"enrichment_target: {target}" if target else "enrichment_target: null"
        content = (
            f"---\ndate: 2026-06-24\nquestion: \"How does combat work?\"\n"
            f"confidence: medium\nenrichment_needed: true\n{target_line}\n---\n\n## Answer\n\nSome answer.\n"
        )
        qfile = tmp_path / "2026-06-24-combat.md"
        qfile.write_text(content)
        return qfile

    def test_sets_enrichment_needed_false(self, tmp_path):
        qfile = self._make_question(tmp_path)
        _clear_enrichment_flag(qfile)
        assert "enrichment_needed: false" in qfile.read_text()

    def test_removes_enrichment_target(self, tmp_path):
        qfile = self._make_question(tmp_path)
        _clear_enrichment_flag(qfile)
        assert "enrichment_target" not in qfile.read_text()

    def test_preserves_rest_of_file(self, tmp_path):
        qfile = self._make_question(tmp_path)
        _clear_enrichment_flag(qfile)
        text = qfile.read_text()
        assert "How does combat work?" in text
        assert "## Answer" in text
        assert "Some answer." in text


def _make_project(tmp_path: Path) -> Path:
    """Scaffold a minimal .knowledge-project layout."""
    (tmp_path / ".knowledge-project").write_text("{}")
    (tmp_path / "kb" / "questions").mkdir(parents=True)
    return tmp_path


def _make_question_file(questions_dir: Path, slug: str, needed: bool, target: str | None) -> Path:
    target_line = f"enrichment_target: {target or 'null'}"
    content = (
        f"---\ndate: 2026-06-24\nquestion: \"Test question\"\n"
        f"confidence: medium\nenrichment_needed: {'true' if needed else 'false'}\n{target_line}\n---\n\n## Answer\n\nSome answer.\n"
    )
    qfile = questions_dir / f"2026-06-24-{slug}.md"
    qfile.write_text(content)
    return qfile


class TestRunEnrich:
    def test_no_gaps_prints_message(self, tmp_path, capsys):
        root = _make_project(tmp_path)
        _make_question_file(root / "kb" / "questions", "q1", needed=False, target=None)
        run_enrich(root)
        assert "No enrichment gaps" in capsys.readouterr().out

    def test_open_gap_no_kb_page(self, tmp_path, capsys):
        root = _make_project(tmp_path)
        _make_question_file(root / "kb" / "questions", "combat", needed=True, target="concepts/combat.md")
        run_enrich(root)
        out = capsys.readouterr().out
        assert "Open enrichment gaps" in out
        assert "concepts/combat" in out

    def test_gap_with_thin_page_not_auto_cleared(self, tmp_path, capsys):
        root = _make_project(tmp_path)
        qfile = _make_question_file(root / "kb" / "questions", "combat", needed=True, target="concepts/combat.md")
        page_dir = root / "kb" / "concepts"
        page_dir.mkdir(parents=True)
        (page_dir / "combat.md").write_text(
            _FRONTMATTER + "# Combat\n\nThe combat system.\n\n**Type:** concept\n"
        )
        run_enrich(root)
        assert "enrichment_needed: true" in qfile.read_text()

    def test_gap_with_enriched_page_is_auto_cleared(self, tmp_path, capsys):
        root = _make_project(tmp_path)
        qfile = _make_question_file(root / "kb" / "questions", "combat", needed=True, target="concepts/combat.md")
        page_dir = root / "kb" / "concepts"
        page_dir.mkdir(parents=True)
        (page_dir / "combat.md").write_text(
            _FRONTMATTER + "# Combat\n\nThe combat system.\n\n## Attacking\n\nRoll damage.\n"
        )
        run_enrich(root)
        assert "enrichment_needed: false" in qfile.read_text()
        assert "Clearing" in capsys.readouterr().out

    def test_no_questions_dir(self, tmp_path, capsys):
        (tmp_path / ".knowledge-project").write_text("{}")
        run_enrich(tmp_path)
        assert "No questions found" in capsys.readouterr().out
