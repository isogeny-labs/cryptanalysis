#!/usr/bin/env python3
"""Recover only the reviewed Hecke input hashes; never regenerate evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "artifacts"))
from artifacts import Config, Remote


def recover(root: Path, remote: Remote, relative: str, digest: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("invalid SHA-256")
    target = root / relative
    if not relative.startswith("experiments/") or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("input path must remain under this repository's experiments directory")
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError("present input differs from its frozen hash")
        return {"path": relative, "sha256": digest, "bytes": target.stat().st_size, "status": "verified_present"}
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        downloaded = Path(temporary) / "input"
        remote.get(digest, downloaded)
        if hashlib.sha256(downloaded.read_bytes()).hexdigest() != digest:
            raise ValueError("store object differs from its content-addressed key")
        staged = target.with_name(target.name + f".repair-{os.getpid()}")
        try:
            shutil.copyfile(downloaded, staged)
            os.replace(staged, target)
        finally:
            staged.unlink(missing_ok=True)
    return {"path": relative, "sha256": digest, "bytes": target.stat().st_size, "status": "recovered_verified"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("tools/ci/hecke_required_inputs.json"))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    manifest = json.loads(args.manifest.read_text())
    if manifest.get("schema") != "hecke.repair-inputs/v1":
        parser.error("unexpected input manifest schema")
    remote = Remote(Config.load(root))
    rows = []
    for relative, digest in sorted(manifest["files"].items()):
        try:
            row = recover(root, remote, relative, digest)
            if args.export:
                exported = args.export / relative
                exported.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / relative, exported)
        except (Exception, SystemExit) as error:
            row = {"path": relative, "sha256": digest, "status": "unavailable", "error": str(error)}
        rows.append(row)
        print(row["status"], relative, flush=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"schema": "hecke.input-recovery/v1", "files": rows}, indent=2) + "\n")
    return int(any(row["status"] == "unavailable" for row in rows))


if __name__ == "__main__":
    raise SystemExit(main())
