"""Read-only custody check of the homogeneous S3 cost screen."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    p, f = read("protocol.json"), read("formula_receipt.json")
    pp, c = read("planted_protocol.json"), read("planted_result.json")
    assert p["status"] == "FROZEN_BEFORE_BUILD"
    assert p["source_sha256"] == sha(HERE / "build_rational.py")
    assert p["lean_source_sha256"] == sha(HERE / "HomogeneousS3.lean")
    assert p["lean_stdout_sha256"] == sha(HERE / "lean.stdout")
    for name, digest in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == digest, name
    assert f["status"] == "PASS_FORMULA_BUILD"
    assert f["protocol_sha256"] == sha(HERE / "protocol.json")
    assert f["formula_sha256"] == sha(HERE / "official_q_homogeneous_m10_v1.xcnf")
    assert f["counts"] == {"vars": 431497, "clauses": 331029,
                           "xors": 333883, "roots": 1179,
                           "linear_rows": 17554}
    assert f["formula_bytes"] == (HERE / "official_q_homogeneous_m10_v1.xcnf").stat().st_size
    assert not (HERE / "build.stderr").read_text()
    assert pp["status"] == "FROZEN_BEFORE_PLANTED_CONTROL"
    assert pp["source_sha256"] == sha(HERE / "planted_control.py")
    for name, digest in pp["input_sha256"].items():
        assert sha(pp["inputs"][name]) == digest, name
    assert c["status"] == "PASS_FULL_ASSIGNMENT"
    assert c["protocol_sha256"] == sha(HERE / "planted_protocol.json")
    assert c["formula_counts_before_pins"] == {"vars": 431497, "clauses": 331029,
                                                 "xors": 333883}
    assert c["checked_clauses_after_pins"] == 332220
    assert c["checked_native_xors"] == 333883
    assert set(c["branch_bits"]) == {0, 1}
    assert not (HERE / "planted.stderr").read_text()
    lean = (HERE / "HomogeneousS3.lean").read_text()
    assert all(s not in lean for s in ("sorry", "admit", "sorryAx"))
    out = (HERE / "lean.stdout").read_text()
    for theorem in ("cleared_identity", "cleared_zero_iff",
                    "yNum_factored", "branch_denominator_nonzero"):
        assert f"HomogeneousS3.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in out
    assert not (HERE / "lean.stderr").read_text()
    prior = json.loads(Path(p["inputs"]["prior_formula_receipt"]).read_text())
    assert f["counts"]["vars"] > prior["counts"]["variables"]
    assert f["counts"]["clauses"] > prior["counts"]["clauses"]
    assert f["counts"]["xors"] > prior["counts"]["native_xors"]
    print(json.dumps({"status": "PASS", "formula_counts": f["counts"],
                      "planted": c["status"], "cost_gate": "LARGER_THAN_PRIOR"},
                     sort_keys=True))


if __name__ == "__main__":
    main()
