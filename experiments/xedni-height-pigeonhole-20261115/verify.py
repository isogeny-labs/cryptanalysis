"""Verify the pinned height-pigeonhole Lean proof and its saved build receipt."""

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMAL = HERE / "formal"
NAMES = (
    "coefficientBox_card",
    "coefficientBox_bounded",
    "bounded_relation_of_card_lt",
    "bounded_witness_of_card_lt_on_dependence",
    "bounded_relation_of_height_ball_count",
    "latticeValues_card_le",
    "bounded_relation_of_lattice_representation",
)
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    deps = json.loads((FORMAL / "DEPENDENCIES.json").read_text())
    for name, digest in deps["source_sha256"].items():
        assert sha(FORMAL / name) == digest, name
    seal = json.loads((HERE / "post-build.json").read_text())
    for name, digest in seal["sha256"].items():
        assert sha(HERE / name) == digest, name
    source = (FORMAL / "HeightPigeonhole.lean").read_text()
    assert not re.search(r"\b(?:sorry|admit|sorryAx|native_decide)\b", source)
    assert not re.search(r"\baxiom\s+", source)
    output = (FORMAL / "build-output.txt").read_text()
    assert "Build completed successfully" in output
    assert "error:" not in output
    for name in NAMES:
        pattern = rf"'XedniHeightPigeonhole\.{name}' depends on axioms: \[([^\]]+)\]"
        matches = re.findall(pattern, output, re.S)
        assert len(matches) == 1, name
        assert set(map(str.strip, matches[0].split(","))) == STANDARD_AXIOMS, name
    print(json.dumps({"status": "PASS", "checked_theorems": len(NAMES),
                      "source_sha256": sha(FORMAL / "HeightPigeonhole.lean")}, sort_keys=True))


if __name__ == "__main__":
    main()
