#!/usr/bin/env python3
"""List storage-backed files directly named by PCC claims."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def claim_artifact_paths(root: Path) -> list[str]:
    out: set[str] = set()
    for claim in sorted((root / "pcc/claims").glob("*.json")):
        for name in strings(json.loads(claim.read_text(encoding="utf-8"))):
            if not name.startswith(("docs/", "experiments/")):
                continue
            rel = PurePosixPath(name)
            if ".." in rel.parts or rel.is_absolute():
                raise ValueError(f"claim names an invalid artifact path: {name}")
            manifest = root / rel.parent / ".artifacts.json"
            if not manifest.is_file():
                continue
            files = json.loads(manifest.read_text(encoding="utf-8")).get("files", {})
            if rel.name in files:
                out.add(name)
    return sorted(out)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    for name in claim_artifact_paths(root):
        print(name)
