#!/usr/bin/env python3
"""Dependency-free structural and release validator for one-day-intern."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path


BEATS = [f"beat-e{i:02d}.md" for i in range(1, 11)]
REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "assets/diary-template.html",
    "references/lark-cli-contract.md",
    "references/artifact-adapters.md",
    "references/data-dashboard.md",
    "references/landing-orientation.md",
    "references/permission-setup.md",
    "references/runtime-compression.md",
    "references/prd-task.md",
    "references/timeline.md",
    "references/world-and-personas.md",
    "scripts/state-tool.py",
    "scripts/build-release.py",
    "scripts/render-diary.py",
] + [f"references/{beat}" for beat in BEATS]


def fail(message: str) -> None:
    raise ValueError(message)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        fail("invalid SKILL.md frontmatter")
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            fail(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"\'')
    return result


def source_files(skill_dir: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store" or "__pycache__" in path.parts:
            continue
        result[path.relative_to(skill_dir).as_posix()] = path.read_bytes()
    return result


def validate_links(skill_dir: Path) -> None:
    pattern = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
    for path in skill_dir.rglob("*.md"):
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            if re.match(r"^(?:https?:|mailto:)", target):
                continue
            if not (path.parent / target).resolve().exists():
                fail(f"broken link in {path}: {target}")


def validate_skill(skill_dir: Path) -> None:
    for relative in REQUIRED:
        if not (skill_dir / relative).is_file():
            fail(f"missing required file: {relative}")
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(skill_text)
    if set(frontmatter) != {"name", "description"}:
        fail("frontmatter must contain only name and description")
    if frontmatter["name"] != skill_dir.name or not re.fullmatch(r"[a-z0-9-]{1,64}", frontmatter["name"]):
        fail("invalid skill name")
    if not frontmatter["description"] or len(frontmatter["description"]) > 1024:
        fail("invalid description")
    if len(skill_text.splitlines()) >= 500:
        fail("SKILL.md must remain below 500 lines")
    for needle in (
        '"schema_version": 4',
        '"room_layout": "company_with_role_rooms"',
        "status=finalizing",
        "paused=true",
        "lease-acquire",
        "task_progress",
        "session_deadline_at",
        "checkpoint_budget",
        "task.task.update_user_access_v2",
        "docs +fetch",
        "drive +add-comment",
        "最多一次微修订",
        "landing-orientation.md",
        "data-dashboard.md",
        "开局前必须阅读",
    ):
        if needle not in skill_text:
            fail(f"SKILL.md missing reliability contract: {needle}")
    contract = (skill_dir / "references/lark-cli-contract.md").read_text(encoding="utf-8")
    if "task +comment" in contract and "不要使用 `task +comment`" not in contract:
        fail("non-idempotent task comments are enabled")
    if "task +update" not in contract or "task tasks get" not in contract:
        fail("deterministic task snapshot reconciliation is incomplete")
    for needle in (
        "company",
        "mentor_dm",
        "boss_dm",
        "permission_grant.status",
        "task.task.update_user_access_v2",
        "docs +fetch",
        "drive +add-comment",
        "task +reopen",
        "尚未检测到修改",
    ):
        if needle not in contract:
            fail(f"CLI contract missing v0.4 workflow: {needle}")
    orientation = (skill_dir / "references/landing-orientation.md").read_text(encoding="utf-8")
    for needle in ("https://wqua64v2akt.feishu.cn/docx/TCwtdW1EKoWtOUxtySbc9JJtnQb", "tenant_readable", "initializing"):
        if needle not in orientation:
            fail(f"landing orientation contract missing: {needle}")
    permissions = (skill_dir / "references/permission-setup.md").read_text(encoding="utf-8")
    for needle in (
        "missing_scopes",
        "console_url",
        "im.message.receive_v1",
        "继续实习",
        "task",
        "calendar",
        "sheets",
        "docs",
        "云文档评论",
    ):
        if needle not in permissions:
            fail(f"permission setup contract missing: {needle}")
    dashboard = (skill_dir / "references/data-dashboard.md").read_text(encoding="utf-8")
    for needle in (
        "sheets +workbook-create",
        "sheets +chart-create",
        "+workbook-info",
        "+csv-get",
        "+chart-list",
        "+revision-get",
        "三个指标的分母不同",
        "不得退回聊天逐条发送 KPI",
    ):
        if needle not in dashboard:
            fail(f"data dashboard contract missing: {needle}")
    openai = (skill_dir / "agents/openai.yaml").read_text(encoding="utf-8")
    for key in ("display_name:", "short_description:", "default_prompt:"):
        if key not in openai:
            fail(f"openai.yaml missing {key}")
    validate_links(skill_dir)


def validate_zip(skill_dir: Path, release_zip: Path) -> None:
    expected = source_files(skill_dir)
    prefix = f".agents/skills/{skill_dir.name}/"
    with zipfile.ZipFile(release_zip) as archive:
        actual = {
            name[len(prefix):]: archive.read(name)
            for name in archive.namelist()
            if name.startswith(prefix) and not name.endswith("/")
        }
    if set(actual) != set(expected):
        fail(f"release file set differs: missing={sorted(set(expected)-set(actual))}, extra={sorted(set(actual)-set(expected))}")
    mismatched = [name for name in expected if expected[name] != actual[name]]
    if mismatched:
        fail(f"release content differs: {mismatched}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--release-zip", type=Path)
    args = parser.parse_args()
    try:
        validate_skill(args.skill_dir)
        if args.release_zip:
            validate_zip(args.skill_dir, args.release_zip)
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    digest = hashlib.sha256((args.skill_dir / "SKILL.md").read_bytes()).hexdigest()
    print(f"skill valid; SKILL.md sha256={digest}")
    if args.release_zip:
        print("release zip matches source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
