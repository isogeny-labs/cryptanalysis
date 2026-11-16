#!/usr/bin/env python3
"""Build the pinned field-fiber identities and inspect every transitive axiom list.

This checks the six ring identities only. Fiber completeness, primitive traces,
and target-group relation sufficiency are separate formal obligations.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PINS = {'FieldFibers.lean': '4619833d39918f1387ff09df786b2893ba8bf68b07ae26e0f5a7ea3ed73d340c', 'lakefile.lean': 'f16d28347a1566ca7a1dc14afd7b1ef9cd1cb52a9892dabe6a8558aba82ba141', 'lean-toolchain': 'ca5f1f601d34c49079e38d7e7041eb0f2a9c227fbc1df0f404820069a052330c', 'lake-manifest.json': '3313a5f8f828f1c8dc61a416d163da53d69b516766ff8d2e311dfb95d7a6d3b2'}
NAMES = {"opposite_pair", "cube_trace", "seventh_trace", "torus_push", "terminal_pair", "orbit_discriminant"}
PREFIX = "AuxiliaryIC.FieldFibers."


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_inputs():
    for name, expected in PINS.items():
        path = HERE / name
        require(path.is_file() and not path.is_symlink(), "plain input required: " + name)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "input pin mismatch: " + name)
    manifest = json.loads((HERE / "lake-manifest.json").read_text())
    mathlib = [p for p in manifest["packages"] if p["name"] == "mathlib"]
    require(len(mathlib) == 1 and mathlib[0]["rev"] == "cfc55fc58714a59dc06e6e79edc6d1d95140d3c2", "Mathlib revision mismatch")
    source = (HERE / "FieldFibers.lean").read_text()
    require(not re.search(r"\b(?:sorry|admit|sorryAx|native_decide|axiom|unsafe|implemented_by|extern|skipKernelTC)\b|#exit", source), "proof escape token")
    declared = re.findall(r"^theorem\s+(\w+)", source, re.MULTILINE)
    requested = re.findall(r"^#print axioms\s+(\w+)", source, re.MULTILINE)
    require(set(declared) == set(requested) == NAMES and len(declared) == len(requested) == 6, "incomplete declaration inspection")


def run(command):
    try:
        result = subprocess.run(command, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=800)
    except subprocess.TimeoutExpired as error:
        for partial in (error.stdout, error.stderr):
            if partial:
                print(partial.decode(errors="replace") if isinstance(partial, bytes) else partial, file=sys.stderr)
        raise
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode:
        print(result.stdout, file=sys.stderr, end="")
    require(result.returncode == 0, "native command failed: " + repr(command))
    return result.stdout


def main(config_only=False):
    check_inputs()
    lake = os.environ.get("AUXILIARY_IC_LAKE") or shutil.which("lake") or str(Path.home() / ".elan/bin/lake")
    require(Path(lake).is_file(), "lake is unavailable; install the pinned toolchain")
    version = run([lake, "env", "lean", "--version"])
    require("version 4.35.0" in version and "rc" not in version, "wrong Lean release: " + version)
    ring = HERE / ".lake/packages/mathlib/.lake/build/lib/lean/Mathlib/Tactic/Ring.olean"
    if not ring.is_file():
        cache_output = run([lake, "exe", "cache", "get", "Mathlib.Tactic.Ring"])
        print(cache_output, file=sys.stderr, end="")
    with tempfile.TemporaryDirectory(prefix="auxiliary-ic-lean-") as scratch:
        output = run([lake, "env", "lean", "-o", str(Path(scratch) / "FieldFibers.olean"), "FieldFibers.lean"])
        require((Path(scratch) / "FieldFibers.olean").is_file(), "native module was not produced")
    rows = re.findall(r"^'([^']+)' depends on axioms: \[([^]]*)\]$", output, re.MULTILINE)
    free = re.findall(r"^'([^']+)' does not depend on any axioms$", output, re.MULTILINE)
    actual = [name for name, _ in rows] + free
    require(set(actual) == {PREFIX + n for n in NAMES} and len(actual) == 6, "incomplete native theorem output")
    require(all({a.strip() for a in axioms.split(",") if a.strip()} <= {"propext", "Classical.choice", "Quot.sound"} for _, axioms in rows), "unexpected theorem foundation")
    check_inputs()
    if config_only:
        print(output, file=sys.stderr, end="")
        print("Field-fiber build configuration and native identities verified")
    else:
        print(output, end="")
        print("Field-fiber ring identities and project binding verified")


if __name__ == "__main__":
    main()
