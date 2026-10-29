#!/usr/bin/env python3
"""Replay submitted certificates without changing their frozen evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

REPOSITORY = Path(__file__).resolve().parents[2]
MANIFEST = REPOSITORY / "tools/ci/quartic_certificates.json"
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def verify_inputs(root, expected):
    """Refuse missing, changed, or escaping inputs before reading certificates."""
    root = root.resolve()
    failures = []
    for name, digest in expected.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe input path: {name}")
        path = root / relative
        if not path.resolve().is_relative_to(root):
            raise ValueError(f"input escapes replay root: {name}")
        if not path.is_file():
            failures.append({"path": name, "error": "missing"})
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            failures.append({"path": name, "error": "digest mismatch"})
    return failures


def audit_axioms(source, output):
    if re.search(r"\b(sorry|admit|native_decide|axiom)\b", source):
        raise ValueError("unverified proof construct in source")
    requested = len(re.findall(r"^#print axioms ", source, re.MULTILINE))
    dependencies = re.findall(r"depends on axioms:\s*\[([^]]*)\]", output)
    free = output.count("does not depend on any axioms")
    if not requested or requested != free + len(dependencies):
        raise ValueError("missing axiom audit output")
    for dependency in dependencies:
        if not set(x.strip() for x in dependency.split(",")) <= STANDARD_AXIOMS:
            raise ValueError(f"nonstandard proof axiom: {dependency}")
    if "sorryAx" in output or "declaration uses" in output:
        raise ValueError("unverified declaration in checker output")
    return requested


def command(arguments, directory, log, timeout=240):
    try:
        result = subprocess.run(arguments, cwd=directory, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout)
        output, code = result.stdout, result.returncode
    except subprocess.TimeoutExpired as error:
        output, code = (error.stdout or b"") + b"\nREPLAY_TIMEOUT\n", 124
    log.write_bytes(output)
    return code, output.decode("utf-8", errors="replace")


def formal(manifest, evidence):
    sources = {row["path"]: row["sha256"] for row in manifest["formal"]}
    failures = verify_inputs(REPOSITORY, sources)
    if failures:
        raise ValueError(f"proof source mismatch: {failures}")
    project = evidence / "proof-project"
    project.mkdir()
    shared = REPOSITORY / manifest["project"]
    for name in ("lakefile.toml", "lake-manifest.json", "lean-toolchain"):
        shutil.copyfile(shared / name, project / name)
    if (project / "lean-toolchain").read_text().strip() != manifest["toolchain"]:
        raise ValueError("unexpected toolchain")
    lock = json.loads((project / "lake-manifest.json").read_text())
    mathlib = next(p for p in lock["packages"] if p["name"] == "mathlib")
    if mathlib["rev"] != manifest["mathlib"]:
        raise ValueError("unexpected Mathlib revision")
    os.environ["MATHLIB_NO_CACHE_ON_UPDATE"] = "1"
    code, output = command(["lake", "exe", "cache", "get", *manifest["imports"]],
                           project, evidence / "mathlib-cache.txt", timeout=1200)
    if code:
        raise ValueError(f"pinned dependency restore failed ({code}): {output[-2000:]}")
    rows = []
    for index, entry in enumerate(manifest["formal"]):
        source = REPOSITORY / entry["path"]
        code, output = command(["lake", "env", "lean", str(source)], project,
                               evidence / f"formal-{index:02d}.txt")
        row = {"path": entry["path"], "returncode": code}
        if code == 0:
            try:
                row["axiom_reports"] = audit_axioms(source.read_text(), output)
            except ValueError as error:
                row["error"] = str(error)
        rows.append(row)
        print(json.dumps(row), flush=True)
    return rows


def integer(manifest, evidence, root):
    root = root.resolve()
    # Original absolute paths are part of several frozen protocols and command
    # receipts. Recreate that layout in a disposable CI copy, never this checkout.
    if root == REPOSITORY or str(root) != manifest["original_root"]:
        raise ValueError("integer replay requires the separate original-layout copy")
    failures = verify_inputs(root, manifest["inputs"])
    if failures:
        raise ValueError(f"frozen input mismatch: {failures}")
    rows = []
    for index, entry in enumerate(manifest["integer"]):
        code, _ = command([sys.executable, str(root / entry["path"])], root,
                          evidence / f"integer-{index:02d}.txt")
        row = {"path": entry["path"], "returncode": code}
        rows.append(row)
        print(json.dumps(row), flush=True)
    failures = verify_inputs(root, manifest["inputs"])
    if failures:
        rows.append({"error": "frozen bytes changed during replay", "files": failures})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("formal", "integer"))
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    args.evidence.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    try:
        if args.mode == "formal":
            rows = formal(manifest, args.evidence)
        else:
            if args.root is None:
                raise ValueError("--root is required for integer replay")
            rows = integer(manifest, args.evidence, args.root)
    except (ValueError, OSError, StopIteration) as error:
        rows = [{"error": str(error)}]
    (args.evidence / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
    return int(any(row.get("returncode", 0) or "error" in row for row in rows))


if __name__ == "__main__":
    raise SystemExit(main())
