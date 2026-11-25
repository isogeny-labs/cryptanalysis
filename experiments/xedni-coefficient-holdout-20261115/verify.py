"""Check frozen source bindings, first-hit audits, Lean axioms and file seal."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRAIN = HERE.parent / "xedni-coefficient-family-control-20261115"
HOLD = HERE.parent / "xedni-nonisomorphic-holdout-20261115"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    old = json.loads((HERE / "result-precompute.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    assert result["status"] == audit["status"] == "PASS"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert old["protocol_sha256"] == sha(HERE / "protocol-initial.json")
    assert old["source_sha256"] == sha(HERE / "run_precompute.py")
    assert protocol["training_family_protocol_sha256"] == sha(TRAIN / "protocol.json")
    assert protocol["training_family_source_sha256"] == sha(TRAIN / "run.py")
    assert protocol["holdout_selection_sha256"] == sha(HOLD / "selection.json")
    assert protocol["holdout_relation_result_sha256"] == sha(HOLD / "relation-result.json")
    assert result["holdout_result_sha256"] == protocol["holdout_relation_result_sha256"]
    assert len(result["fields"]) == len(old["fields"]) == len(audit["fields"]) == 8
    for row, previous, checked in zip(result["fields"],old["fields"],audit["fields"]):
        assert row["first_family"]["query_index_one_based"] == checked["family_first_query"] == 35
        assert row["first_family"]["vector_tests_to_hit"] == checked["family_vector_tests"] == 452
        assert row["first_family"]["group_add_calls_to_hit"] == checked["family_group_add_calls"] == 3065
        assert row["first_family"]["t"] == previous["first_family"]["t"]
        assert row["first_family"]["vector"] == previous["first_family"]["vector"] == [1,1]
        assert row["prefix_sha256"] == previous["prefix_sha256"] == sha(HERE / row["prefix_path"])
        assert row["first_fixed_vector"]["query_index_one_based"] == checked["fixed_first_query"]
        assert row["first_rational"]["query_index_one_based"] == checked["rational_first_query"]
    assert (HERE / "run.stderr").read_bytes() == b""
    assert (HERE / "audit.stderr").read_bytes() == b""
    formal = HERE / "formal"
    assert (formal / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.35.0-rc4"
    manifest = json.loads((formal / "lake-manifest.json").read_text())
    mathlib = [p for p in manifest["packages"] if p["name"] == "mathlib"]
    assert len(mathlib) == 1 and mathlib[0]["rev"] == "021c46bdd042f67b538b9f9871d556a93713a9a9"
    source = (formal / "FirstFamilyHit.lean").read_text()
    for forbidden in (r"\bsorry\b",r"\badmit\b",r"\bsorryAx\b",r"\bnative_decide\b",r"\baxiom\s+"):
        assert re.search(forbidden, source) is None
    build = (formal / "build-output.txt").read_text()
    assert "Build completed successfully (3138 jobs)." in build
    names = ("vector_image_eq_family","relation_at_34") + tuple(f"no_relation_before_34_{q}" for q in (751,883,983,1103,1153,1453,1459))
    for name in names:
        lines = [line for line in build.splitlines() if f"{name}' depends on axioms:" in line]
        assert len(lines) == 1
        axioms = lines[0].split("depends on axioms: [",1)[1].rstrip("]").split(", ")
        assert set(axioms) <= {"propext","Classical.choice","Quot.sound"}
    for line in (HERE / "SEAL.sha256").read_text().splitlines():
        digest, rel = line.split("  ",1)
        assert sha(HERE / rel) == digest, rel
    print(json.dumps({"schema":"xedni-coefficient-holdout-verify-v1","status":"PASS",
                      "fields":8,"checked_theorems":len(names)},sort_keys=True))

if __name__ == "__main__":
    main()
