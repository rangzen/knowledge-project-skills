#!/usr/bin/env python3
"""Validate that Markdown links in skill files resolve within each skill."""

import re
import sys
from pathlib import Path


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def iter_skill_files(root: Path) -> list[Path]:
    return sorted((root / "skills").glob("*/SKILL.md"))


def main() -> int:
    root = Path.cwd()
    broken = []
    external = []
    for skill_file in iter_skill_files(root):
        text = skill_file.read_text()
        for match in LINK_RE.findall(text):
            if "://" in match or match.startswith("#"):
                continue
            target = match.split("#", 1)[0]
            target_path = (skill_file.parent / target).resolve()
            skill_dir = skill_file.parent.resolve()
            if not target_path.is_relative_to(skill_dir):
                external.append((skill_file.relative_to(root), match))
            elif not target_path.exists():
                broken.append((skill_file.relative_to(root), match))
    if broken:
        for skill_file, match in broken:
            print(f"BROKEN: {skill_file} -> {match}")
        return 1
    if external:
        for skill_file, match in external:
            print(f"OUTSIDE SKILL: {skill_file} -> {match}")
        return 1
    print(f"OK: validated {len(iter_skill_files(root))} SKILL.md file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
