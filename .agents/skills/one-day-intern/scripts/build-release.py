#!/usr/bin/env python3
"""Build a deterministic Codex skill zip and verify every included byte."""

from __future__ import annotations

import argparse
import hashlib
import os
import zipfile
from pathlib import Path


FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def files(skill_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(skill_dir.rglob("*"))
        if path.is_file() and path.name != ".DS_Store" and "__pycache__" not in path.parts
    ]


def build(skill_dir: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    prefix = Path(".agents") / "skills" / skill_dir.name
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files(skill_dir):
                relative = path.relative_to(skill_dir)
                info = zipfile.ZipInfo((prefix / relative).as_posix(), FIXED_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o755 if path.suffix == ".py" else 0o644) << 16
                archive.writestr(info, path.read_bytes())
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()


def verify(skill_dir: Path, output: Path) -> None:
    prefix = f".agents/skills/{skill_dir.name}/"
    expected = {path.relative_to(skill_dir).as_posix(): path.read_bytes() for path in files(skill_dir)}
    with zipfile.ZipFile(output) as archive:
        actual = {
            name[len(prefix):]: archive.read(name)
            for name in archive.namelist()
            if name.startswith(prefix) and not name.endswith("/")
        }
    if set(expected) != set(actual):
        raise ValueError("release file set does not match source")
    mismatched = [name for name in expected if expected[name] != actual[name]]
    if mismatched:
        raise ValueError(f"release bytes differ: {mismatched}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("output_zip", type=Path)
    args = parser.parse_args()
    build(args.skill_dir.resolve(), args.output_zip.resolve())
    verify(args.skill_dir.resolve(), args.output_zip.resolve())
    digest = hashlib.sha256(args.output_zip.read_bytes()).hexdigest()
    print(f"built {args.output_zip} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
