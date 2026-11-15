"""Audit the pinned Lean recovery module and its saved kernel build output."""

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent / "formal"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    deps = json.loads((HERE / "DEPENDENCIES.json").read_text())
    for name, digest in deps["sha256"].items():
        assert sha(HERE / name) == digest, name
    manifest = json.loads((HERE / "lake-manifest.json").read_text())
    mathlib = next(package for package in manifest["packages"] if package["name"] == "mathlib")
    assert mathlib["rev"] == deps["mathlib_revision"]
    assert deps["mathlib_revision"] in (HERE / "lakefile.toml").read_text()
    assert (HERE / "lean-toolchain").read_text().strip() == deps["lean_toolchain"]
    source = (HERE / "TargetRecovery.lean").read_text()
    for forbidden in (r"\bsorry\b", r"\badmit\b", r"\bsorryAx\b", r"\baxiom\b", r"native_decide"):
        assert not re.search(forbidden, source), forbidden
    output = (HERE / "build-output.txt").read_text()
    assert "Build completed successfully" in output
    assert "error:" not in output
    assert "sorryAx" not in output
    declarations = deps["audited_declarations"]
    for declaration in declarations:
        assert f"#print axioms {declaration}" in source
        line = next(line for line in output.splitlines()
                    if f"'XedniCrtTargetRecovery.{declaration}' depends on axioms:" in line)
        assert "[propext, Classical.choice, Quot.sound]" in line
    assert len(declarations) == 3
    print(json.dumps({"status": "PASS", "checked_theorems": len(declarations),
                      "mathlib_revision": deps["mathlib_revision"],
                      "lean_toolchain": deps["lean_toolchain"]}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
