#!/usr/bin/env python3
"""Fail CI for unsafe skill instructions, obvious secrets, and unpinned actions."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}
REMOTE_SHELL = re.compile(
    r"\b(?:curl|wget)\b[^\n]*(?:\\\n[^\n]*)*\|\s*(?:sh|bash)\b",
    re.IGNORECASE,
)
ACTION_USE = re.compile(r"^\s*uses:\s*(?P<action>\S+)", re.MULTILINE)
SHA = re.compile(r"^[0-9a-f]{40}$")


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    )
    return [ROOT / item for item in result.stdout.decode().split("\0") if item]


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        text = read_text(path)
        if text is None:
            continue
        relative = path.relative_to(ROOT)
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{relative}: possible {name}")
        if relative.parts[:1] == ("skills",) and path.name == "SKILL.md":
            if REMOTE_SHELL.search(text):
                findings.append(f"{relative}: remote download piped to a shell")
        if relative.parts[:2] == (".github", "workflows"):
            for match in ACTION_USE.finditer(text):
                action = match.group("action")
                if action.startswith("./"):
                    continue
                if "@" not in action or not SHA.fullmatch(action.rsplit("@", 1)[1]):
                    findings.append(f"{relative}: action is not pinned to a full commit SHA: {action}")

    if findings:
        print("Security policy check failed:", file=sys.stderr)
        print("\n".join(f"- {finding}" for finding in findings), file=sys.stderr)
        return 1
    print("Security policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
