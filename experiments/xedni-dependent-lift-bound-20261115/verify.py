"""Verify the dependent-lift formalization's source and build receipt."""

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMAL = HERE / "formal"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = json.loads((HERE / "SOURCE.json").read_text())
    assert source["schema"] == "xedni-dependent-lift-source-v1"
    base_bytes = (FORMAL / "XedniObstruction.lean").read_bytes()
    assert sha(FORMAL / "XedniObstruction.lean") == source["base_source_sha256"]
    blob = hashlib.sha1(b"blob " + str(len(base_bytes)).encode() + b"\0" + base_bytes).hexdigest()
    assert blob == source["base_git_blob"]
    height_bytes = (FORMAL / "HeightPigeonhole.lean").read_bytes()
    assert sha(FORMAL / "HeightPigeonhole.lean") == source["height_source_sha256"]
    height_blob = hashlib.sha1(
        b"blob " + str(len(height_bytes)).encode() + b"\0" + height_bytes
    ).hexdigest()
    assert height_blob == source["height_git_blob"]
    assert (FORMAL / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.35.0-rc4"
    manifest = json.loads((FORMAL / "lake-manifest.json").read_text())
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in json.dumps(manifest)
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in (FORMAL / "lakefile.toml").read_text()
    code = (FORMAL / "XedniDependentLift.lean").read_text()
    assert not any(token in code for token in ("sorry", "admit", "sorryAx", "native_decide"))
    assert "axiom " not in code
    output = (FORMAL / "build-output.txt").read_text()
    assert "Build completed successfully" in output
    assert "sorryAx" not in output
    axiom_lines = re.findall(r"'([^']+)' depends on axioms:\s*\[([^\]]*)\]", output)
    assert len(axiom_lines) == 32
    allowed = {"propext", "Classical.choice", "Quot.sound"}
    assert all(set(axioms.replace("\n", "").split(", ")) <= allowed
               for _, axioms in axiom_lines)
    expected = (
        "dependent_lift_sample_count", "mem_boundedCandidates",
        "nontrivial_iff_ne_zero", "boundedCandidates_card",
        "dependent_lift_box_count", "dependent_lift_explicit_count",
        "dependent_lift_height_count", "no_uniform_small_height_cover",
        "no_uniform_rank_gap_cover",
    )
    assert all(any(decl == f"XedniObstruction.{name}"
                   for decl, _ in axiom_lines) for name in expected)
    gate = json.loads((HERE / "parameter_gate.json").read_text())
    assert gate["schema"] == "xedni-dependent-lift-parameter-gate-v1"
    assert [row["subgroup_order"] for row in gate["rows"][::2]] == \
        [43, 53, 53, 79, 61, 73, 47, 71]
    assert all(row["max_radius"] == (1 if row["arity"] == 2 else 0)
               and not row["rank_gap_numerically_possible_with_nonempty_torsion"]
               for row in gate["rows"])
    print(json.dumps({"status": "PASS", "checked_declarations": 32,
                      "base_source_sha256": source["base_source_sha256"],
                      "extension_source_sha256": sha(FORMAL / "XedniDependentLift.lean")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
