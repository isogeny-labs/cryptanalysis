"""Check pinned xedni selection-law sources and saved Lean axiom receipts."""

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMAL = HERE / "formal"
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
NEW_THEOREM = "XedniSelectionLaw.selected_dependent_lift_weight_bound"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    deps = json.loads((FORMAL / "DEPENDENCIES.json").read_text())
    for name, digest in deps["source_sha256"].items():
        assert sha(FORMAL / name) == digest, name
    seal = json.loads((HERE / "post-build.json").read_text())
    for name, digest in seal["sha256"].items():
        assert sha(HERE / name) == digest, name
    for name in ("XedniObstruction.lean", "SelectionLaw.lean"):
        source = (FORMAL / name).read_text()
        assert not re.search(r"\b(?:sorry|admit|sorryAx|native_decide)\b", source)
        assert not re.search(r"\baxiom\s+", source)
    output = (FORMAL / "build-output.txt").read_text()
    assert "Build completed successfully" in output
    assert "error:" not in output
    matches = re.findall(
        rf"'{re.escape(NEW_THEOREM)}' depends on axioms: \[([^\]]+)\]",
        output, re.S)
    assert len(matches) == 1
    assert set(map(str.strip, matches[0].split(","))) == STANDARD_AXIOMS
    imported = re.findall(r"'XedniObstruction\.([^']+)' depends on axioms:", output)
    assert len(imported) == 16, len(imported)
    print(json.dumps({"status": "PASS", "new_theorems": 1,
                      "imported_theorems": len(imported),
                      "source_sha256": sha(FORMAL / "SelectionLaw.lean")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
