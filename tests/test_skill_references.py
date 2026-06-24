"""
Checks that every relative markdown link in a skill's SKILL.md resolves to an
existing file on disk.  Catches the class of drift where a reference is updated
in one place but the target file is renamed or removed.
"""
import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "skills"
SKILL_FILES = list(SKILLS_DIR.glob("*/SKILL.md"))

# Matches [label](path) links; excludes http/https/mailto and bare anchors.
_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def _relative_links(skill_md: Path) -> list[tuple[str, str]]:
    """Return (label, target_path) for every relative link in skill_md."""
    text = skill_md.read_text()
    results = []
    for label, target in _LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # Strip fragment
        path_part = target.split("#")[0]
        if path_part:
            results.append((label, path_part))
    return results


def _cases() -> list[tuple[Path, str, str]]:
    cases = []
    for skill_md in SKILL_FILES:
        for label, target in _relative_links(skill_md):
            cases.append((skill_md, label, target))
    return cases


@pytest.mark.parametrize("skill_md,label,target", _cases(), ids=[
    f"{c[0].parent.name}/{c[2]}" for c in _cases()
])
def test_relative_link_resolves(skill_md: Path, label: str, target: str) -> None:
    resolved = (skill_md.parent / target).resolve()
    assert resolved.exists(), (
        f"{skill_md.relative_to(SKILLS_DIR.parent)}: "
        f"link [{label}]({target}) does not resolve to an existing file"
    )
