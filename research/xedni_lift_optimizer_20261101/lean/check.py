#!/usr/bin/env python3
"""Check the pinned xedni affine-coset proof and its Rust source binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AXIOM_LINE = re.compile(r"'([^']+)' depends on axioms: \[([^]]*)\]")


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=pathlib.Path, default=HERE / "receipt.json")
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    if receipt["schema"] != "cryptanalysis.xedni-affine-lean-receipt/v1":
        raise ValueError("unknown receipt schema")
    for field, relative in (("lean_sha256", "research/xedni_lift_optimizer_20261101/lean/XedniAffineCoset.lean"),
                            ("rust_sha256", "suite/src/cryptanalysis/xedni_lift.rs"),
                            ("toolchain_sha256", "lean-toolchain")):
        actual = digest(ROOT / relative)
        if actual != receipt[field]:
            raise ValueError(f"{relative}: SHA-256 mismatch: {actual}")
    toolchain = (ROOT / "lean-toolchain").read_text().strip()
    if toolchain != receipt["toolchain"]:
        raise ValueError("Lean toolchain changed")
    run = subprocess.run(["lean", str(HERE / "XedniAffineCoset.lean")], cwd=ROOT,
                         capture_output=True, text=True, check=False)
    if run.returncode or run.stderr:
        raise ValueError(f"Lean failed: exit={run.returncode}, stderr={run.stderr!r}")
    matches = AXIOM_LINE.findall(run.stdout)
    if AXIOM_LINE.sub("", run.stdout).strip():
        raise ValueError("unexpected Lean output")
    got = {name: sorted(a.strip() for a in axioms.split(",") if a.strip())
           for name, axioms in matches}
    if len(got) != len(matches) or got != receipt["axioms"]:
        raise ValueError(f"Lean axiom audit mismatch: {got!r}")
    print(run.stdout, end="")
    print("Xedni affine-coset proof and source binding verified")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"proof check failed: {exc}", file=sys.stderr)
        sys.exit(1)
