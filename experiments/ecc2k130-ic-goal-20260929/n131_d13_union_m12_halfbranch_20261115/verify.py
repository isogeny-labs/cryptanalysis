"""Read-only custody check for the half-fixed m12 screen and controls."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    p = read("protocol.json")
    f = read("formula_receipt.json")
    c = read("class_result.json")
    planted_p = read("planted_protocol.json")
    planted = read("planted_result.json")
    sage_p = read("sage_protocol.json")
    sage = read("sage_result.json")
    assert p["status"] == "FROZEN_BEFORE_BUILD"
    assert p["source_sha256"] == sha(HERE / "build_formula.py")
    assert p["class_source_sha256"] == sha(HERE / "class_screen.py")
    for key, digest in p["input_sha256"].items():
        assert sha(p["inputs"][key]) == digest, key
    assert p["fixed_original_positions"] == [0, 2, 4, 6, 8, 10]
    assert p["summand_count"] == 12 and p["target_count"] == 1
    formula = HERE / "official_q_d13_halfbranch_m12_v1.xcnf"
    assert f["status"] == "PASS_FORMULA_BUILD"
    assert f["protocol_sha256"] == sha(HERE / "protocol.json")
    assert f["formula_sha256"] == sha(formula)
    assert f["formula_bytes"] == formula.stat().st_size
    assert f["fixed_original_positions"] == p["fixed_original_positions"]
    assert f["counts"] == {"variables": 379964, "clauses": 346253,
                           "native_xors": 279260, "roots": 2227,
                           "linear_rows": 10742}
    with formula.open() as stream:
        assert stream.readline().strip() == "p cnf 379964 625513"
    assert not (HERE / "build.stderr").read_text()
    assert c["status"] == "PASS_EXACT_CLASS_COUNTS"
    assert c["protocol_sha256"] == sha(HERE / "protocol.json")
    assert c["formula_receipt_sha256"] == sha(HERE / "formula_receipt.json")
    original = c["source_classes"]
    image = c["image_classes"]
    assert original == [2160, 2067, 1974, 2067]
    assert image == [4134, 0, 4134, 0]
    assert c["union_classes"] == [a + b for a, b in zip(original, image)]
    counts = [int(value) for value in c["ordered_raw_tuples_by_cofactor_class"]]
    assert sum(counts) == 8268**6 * 16536**6
    assert all(int(value.split(".")[0]) == 2399143125
               for value in c["conditional_uniform_subgroup_mean_per_endpoint"])
    assert planted_p["source_sha256"] == sha(HERE / "planted_m12.py")
    for key, digest in planted_p["input_sha256"].items():
        assert sha(planted_p["inputs"][key]) == digest, key
    assert planted["status"] == "PASS_FULL_ASSIGNMENT"
    assert planted["protocol_sha256"] == sha(HERE / "planted_protocol.json")
    assert planted["formula_counts_before_pins"] == {"vars": 379964,
                                                      "clauses": 346253,
                                                      "xors": 279260}
    assert planted["checked_native_xors"] == 279260
    assert all(planted["leaf_branch_bits"][i] == 0 for i in p["fixed_original_positions"])
    assert not (HERE / "planted.stderr").read_text()
    assert sage_p["source_sha256"] == sha(HERE / "audit_sage.py")
    assert sage_p["sage_runtime_info_sha256"] == sha(HERE / "sage_runtime_info.json")
    for key, digest in sage_p["input_sha256"].items():
        assert sha(sage_p["inputs"][key]) == digest, key
    assert sage["status"] == "PASS_ALL_TWELVE_LEAVES_AND_TARGET_FIBER"
    assert sage["protocol_sha256"] == sha(HERE / "sage_protocol.json")
    assert (sage["checked_leaves"], sage["checked_partial_sums"],
            sage["checked_target_fiber_endpoints"]) == (12, 10, 4)
    assert not (HERE / "sage.stderr").read_text()
    full = json.loads((EXP / "n131_d13_union_arity_20261115" / "result.json").read_text())
    assert f["counts"]["variables"] < full["rows"]["12"]["formula_counts"]["vars"]
    print(json.dumps({"status": "PASS_FORMULA_CLASS_AND_CONTROLS",
                      "variables": f["counts"]["variables"],
                      "clauses": f["counts"]["clauses"],
                      "xors": f["counts"]["native_xors"]}, sort_keys=True))


if __name__ == "__main__":
    main()
