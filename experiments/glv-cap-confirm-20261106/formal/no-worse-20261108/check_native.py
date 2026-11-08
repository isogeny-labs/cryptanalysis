#!/usr/bin/env python3
"""Natively verify the exact GLV cap proof after binding its published inputs."""

import hashlib
import re
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PROOF = HERE / "NoWorseLogic.lean"
BINDING = HERE / "check_binding.py"
PROOF_SHA256 = "613d9eb1ca98ee95418984b5dac2b8bfcbcd6b705c20b38289bfc93e90a7f2d6"
BINDING_SHA256 = "c3d60acb948277518d810573ebc247b10b0a03f17e3a57ccd9688b1cf8ef3b18"
THEOREMS = frozenset({
    "published_pooled_noWorsePass", "published_pooled_wellFormed",
    "published_j0_straddles_one", "published_j0_point_above_one",
    "published_j0_wellFormed", "published_j0_not_bounded_by_pooled_pass",
    "pooled_pass_does_not_bound_family_upper",
})


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*command: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                            timeout=180, check=False)
    require(result.returncode == 0, f"{command[0]} failed: {result.stdout[-2000:]} {result.stderr[-2000:]}")
    return result


def main() -> None:
    require(ROOT.joinpath("lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1",
            "Lean toolchain pin changed")
    require(digest(PROOF) == PROOF_SHA256 and digest(BINDING) == BINDING_SHA256,
            "proof or binding checker changed without review")
    require(re.search(r"Lean \(version 4\.34\.1,", run("lean", "--version").stdout) is not None,
            "installed Lean version differs from repository pin")
    run(sys.executable, str(BINDING))
    output = run("lean", str(PROOF)).stdout
    printed = re.findall(r"^'GLVCapNoWorse\.([^']+)' does not depend on any axioms$",
                         output, re.MULTILINE)
    require(len(printed) == len(THEOREMS) and set(printed) == THEOREMS,
            "incomplete or changed native axiom output")
    require(digest(PROOF) == PROOF_SHA256 and digest(BINDING) == BINDING_SHA256,
            "proof or binding checker changed during verification")
    print(output, end="")
    print("GLV cap proof and published input binding verified")


if __name__ == "__main__":
    main()
