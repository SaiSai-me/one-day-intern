#!/usr/bin/env python3
"""Render the internship diary with deterministic HTML escaping and atomic output."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


REQUIRED_SCALARS = (
    "player_name",
    "run_id",
    "title",
    "date",
    "status",
    "tasks_completed",
    "review_rounds",
    "work_changes",
    "outcome",
    "ending",
)


def load_data(path: str) -> dict[str, Any]:
    if path == "-":
        value = json.load(sys.stdin)
    else:
        with Path(path).open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("diary data must be a JSON object")
    missing = [key for key in REQUIRED_SCALARS if key not in value]
    if missing:
        raise ValueError(f"missing diary fields: {missing}")
    highlights = value.get("highlights")
    if not isinstance(highlights, list) or not 0 <= len(highlights) <= 5:
        raise ValueError("highlights must contain 0 to 5 factual strings")
    if not all(isinstance(item, str) for item in highlights):
        raise ValueError("every highlight must be a string")
    return value


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render(template: str, data: dict[str, Any]) -> str:
    replacements = {key: escape(data[key]) for key in REQUIRED_SCALARS}
    replacements["outcome"] = escape(data["outcome"]).replace("\n", "<br>")
    replacements["ending"] = escape(data["ending"]).replace("\n", "<br>")
    replacements["highlights"] = "\n      ".join(f"<li>{escape(item)}</li>" for item in data["highlights"])
    pattern = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
    unknown = set(pattern.findall(template)) - replacements.keys()
    if unknown:
        raise ValueError(f"unresolved template placeholders: {sorted(unknown)}")
    return pattern.sub(lambda match: replacements[match.group(1)], template)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--data-file", required=True, help="JSON path, or - for stdin")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = load_data(args.data_file)
        rendered = render(args.template.read_text(encoding="utf-8"), data)
        atomic_write(args.output, rendered)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 1
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
