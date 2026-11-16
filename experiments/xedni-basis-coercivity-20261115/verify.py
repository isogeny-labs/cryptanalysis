"""Verify pinned Lean source and axiom receipts for basis coercivity."""

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMAL = HERE / "formal"
NAMES = (
    "coordinate_bounded_of_height",
    "unshear_shear",
    "shear_unshear",
    "shear_add",
    "shearAddEquiv",
    "squareHeight_pos_of_ne_zero",
    "unbounded_coordinates_in_sheared_basis",
)
STANDARD = {"propext", "Classical.choice", "Quot.sound"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    deps = json.loads((FORMAL / "DEPENDENCIES.json").read_text())
    for name, digest in deps["source_sha256"].items():
        assert sha(FORMAL / name) == digest, name
    seal = json.loads((HERE / "post-build.json").read_text())
    for name, digest in seal["sha256"].items():
        assert sha(HERE / name) == digest, name
    source = (FORMAL / "BasisCoercivity.lean").read_text()
    assert not re.search(r"\b(?:sorry|admit|sorryAx|native_decide)\b", source)
    assert not re.search(r"\baxiom\s+", source)
    output = (FORMAL / "build-output.txt").read_text()
    assert "Build completed successfully" in output
    assert "error:" not in output
    for name in NAMES:
        pat = rf"'XedniBasisCoercivity\.{name}' depends on axioms: \[([^\]]+)\]"
        matches = re.findall(pat, output, re.S)
        assert len(matches) == 1, name
        axioms = set(map(str.strip, matches[0].split(",")))
        assert axioms <= STANDARD, (name, axioms)
    print(json.dumps({"status": "PASS", "checked_declarations": len(NAMES),
                      "source_sha256": sha(FORMAL / "BasisCoercivity.lean")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
