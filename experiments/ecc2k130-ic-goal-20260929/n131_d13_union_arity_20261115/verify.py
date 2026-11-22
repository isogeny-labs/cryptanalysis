"""Read-only custody and arithmetic check for the N131 union arity screen."""

import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def convolution(left, right):
    return [sum(left[j]*right[(i-j)%4] for j in range(4))
            for i in range(4)]


def main():
    p, result = read("protocol.json"), read("result.json")
    pp, planted = read("planted_protocol.json"), read("planted_result.json")
    sp, sage = read("sage_protocol.json"), read("sage_result.json")
    assert p["status"] == "FROZEN_BEFORE_SCREEN"
    assert p["source_sha256"] == sha(HERE / "screen.py")
    for name, digest in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == digest, name
    assert result["status"] == "PASS_EXACT_FORMULA_AND_CLASS_COUNTS"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    census = json.loads(Path(p["inputs"]["raw_census"]).read_text())
    classes = [census["original_cofactor_classes_per_position"][str(i)]
               + census["image_cofactor_classes_per_position"][str(i)]
               for i in range(4)]
    assert sum(classes) == result["raw_choices_per_position"] == 16536
    getcontext().prec = 55
    r = int(result["subgroup_order"])
    for m in (11, 12):
        row = result["rows"][str(m)]
        x = [1, 0, 0, 0]
        for _ in range(m):
            x = convolution(x, classes)
        assert [str(v) for v in x] == row["ordered_raw_tuples_by_cofactor_class"]
        assert [str(Decimal(v)/Decimal(r)) for v in x] == row["conditional_uniform_subgroup_mean_per_endpoint"]
        output = HERE / f"official_q_union_m{m}.xcnf"
        assert row["formula_sha256"] == sha(output)
        assert row["formula_bytes"] == output.stat().st_size
    assert result["rows"]["11"]["formula_counts"] == {
        "vars": 376282, "clauses": 343691, "xors": 274738,
        "roots": 2751, "linear_rows": 19257}
    assert result["rows"]["12"]["formula_counts"] == {
        "vars": 414775, "clauses": 378221, "xors": 302885,
        "roots": 3013, "linear_rows": 20960}
    assert not (HERE / "screen.stderr").read_text()
    assert pp["status"] == "FROZEN_BEFORE_PLANTED_CONTROL"
    assert pp["source_sha256"] == sha(HERE / "planted_m12.py")
    for name, digest in pp["input_sha256"].items():
        assert sha(pp["inputs"][name]) == digest, name
    assert planted["status"] == "PASS_FULL_ASSIGNMENT"
    assert planted["protocol_sha256"] == sha(HERE / "planted_protocol.json")
    assert planted["formula_counts_before_pins"] == {
        "vars": 414775, "clauses": 378221, "xors": 302885}
    assert planted["checked_clauses_after_pins"] == 381273
    assert planted["checked_native_xors"] == 302885
    assert len(planted["leaf_codes"]) == 12
    assert set(planted["leaf_branch_bits"]) == {0, 1}
    assert not (HERE / "planted.stderr").read_text()
    assert sp["status"] == "FROZEN_BEFORE_INDEPENDENT_REPLAY"
    assert sp["source_sha256"] == sha(HERE / "audit_sage.py")
    assert sp["sage_runtime_info_sha256"] == sha(HERE / "sage_runtime_info.json")
    for name, digest in sp["input_sha256"].items():
        assert sha(sp["inputs"][name]) == digest, name
    assert sage["status"] == "PASS_ALL_TWELVE_LEAVES_AND_TARGET_FIBER"
    assert sage["protocol_sha256"] == sha(HERE / "sage_protocol.json")
    assert (sage["checked_leaves"], sage["checked_partial_sums"],
            sage["checked_target_fiber_endpoints"]) == (12, 10, 4)
    assert not (HERE / "sage.stderr").read_text()
    print(json.dumps({"status": "PASS", "arities": [11, 12],
                      "m12_planted": planted["status"],
                      "m12_sage": sage["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
