"""Verify the pinned sampled-witness Lean build and its saved evidence."""

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMAL = HERE / "formal"

NAMES = (
    "relation_reduces", "no_dependent_lift", "all_compatible_lifts_blocked",
    "dotHom_surjective", "zero_relation_fiber_count", "zeroFiber_count",
    "bounded_relation_union_count", "intCast_ne_zero_of_natAbs_lt",
    "bounded_intVector_cast_nonzero", "integer_candidate_union_count",
    "xedniSampleMap_involutive", "xedniSampleMap_bijective",
    "xedni_sample_event_card", "sampled_integer_candidate_union_count",
    "dependent_lift_sample_count",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    deps = json.loads((FORMAL / "DEPENDENCIES.json").read_text())
    for name, digest in deps["source_sha256"].items():
        assert sha(FORMAL / name) == digest, name
    seal = json.loads((HERE / "post-build.json").read_text())
    for name, digest in seal["sha256"].items():
        assert sha(HERE / name) == digest, name
    source = (FORMAL / "XedniObstruction.lean").read_text()
    assert not re.search(r"\b(?:sorry|admit|sorryAx|native_decide)\b", source)
    assert "axiom " not in source
    output = (FORMAL / "build-output.txt").read_text()
    assert "Build completed successfully" in output
    assert "error:" not in output
    for name in NAMES:
        lines = [line for line in output.splitlines()
                 if f"XedniObstruction.{name}' depends on axioms:" in line]
        assert len(lines) == 1, name
        assert lines[0].endswith("[propext, Classical.choice, Quot.sound]") or lines[0].endswith(
            "[propext, Quot.sound]"), name
    assert "sorryAx" not in output
    print(json.dumps({"status": "PASS", "checked_theorems": len(NAMES),
                      "source_sha256": sha(FORMAL / "XedniObstruction.lean")}, sort_keys=True))


if __name__ == "__main__":
    main()
