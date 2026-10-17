#!/usr/bin/env python3
"""Validate the current skill's references and deterministic release contents."""
from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path

REQUIRED = {"SKILL.md", "agents/openai.yaml", "references/scenario.md", "references/runtime.md",
            "references/workflow.md", "assets/work-materials.md", "assets/prd.md",
            "assets/diary-template.html", "assets/landing.md", "assets/prototype.svg", "scripts/state-tool.py", "scripts/render-diary.py",
            "scripts/build-release.py", "scripts/validate-skill.py", "tests/test_workflow.py"}


def source_files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and p.name != ".DS_Store" and "__pycache__" not in p.parts}


def validate_skill(root):
    files = source_files(root)
    if REQUIRED - files.keys():
        raise ValueError(f"missing: {sorted(REQUIRED - files.keys())}")
    if any("live-demo" in p or "demo-cues" in p or "runtime-compression" in p or "beat-e" in p for p in files):
        raise ValueError("historical runtime found in current distribution")
    text = files["SKILL.md"].decode()
    if not re.match(r"^---\nname: one-day-intern\ndescription: .+\n---", text):
        raise ValueError("invalid skill frontmatter")
    if len(text.splitlines()) >= 500:
        raise ValueError("entrypoint is too long")
    for path in root.rglob("*.md"):
        for target in re.findall(r"\[[^\]]*\]\(([^)#]+)(?:#[^)]+)?\)", path.read_text()):
            if re.match(r"^(https?:|mailto:)", target):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                raise ValueError(f"broken or external package link: {path}: {target}")
    metadata = files["agents/openai.yaml"].decode()
    if "$one-day-intern" not in metadata or "六分钟" in metadata or "完整版" in metadata:
        raise ValueError("metadata must advertise the single version")


def validate_zip(root, archive_path):
    prefix = ".agents/skills/one-day-intern/"
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names) or any(not name.startswith(prefix) for name in names):
            raise ValueError("unexpected archive entries")
        actual = {name[len(prefix):]: archive.read(name) for name in names}
    if source_files(root) != actual:
        raise ValueError("release differs from current source")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("skill_dir", type=Path)
    p.add_argument("--release-zip", type=Path)
    args = p.parse_args()
    try:
        validate_skill(args.skill_dir)
        if args.release_zip:
            validate_zip(args.skill_dir, args.release_zip)
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        p.exit(1, f"validation failed: {exc}\n")
    print("single-version skill valid" + ("; release matches source" if args.release_zip else ""))


if __name__ == "__main__":
    main()
