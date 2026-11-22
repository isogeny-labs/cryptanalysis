"""Read-only custody and result check for the union ten-leaf formula."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def check_inputs(protocol):
    for name, digest in protocol["input_sha256"].items():
        assert sha(protocol["inputs"][name]) == digest, name


def main():
    p = read("protocol.json")
    formula = read("formula_receipt.json")
    pp = read("planted_protocol.json")
    planted = read("planted_result.json")
    sp = read("sage_protocol.json")
    sage = read("sage_result.json")
    assert p["status"] == "FROZEN_BEFORE_BUILD"
    assert p["source_sha256"] == sha(HERE / "build_formula.py")
    check_inputs(p)
    assert formula["status"] == "PASS_FORMULA_BUILD"
    assert formula["protocol_sha256"] == sha(HERE / "protocol.json")
    assert formula["formula_sha256"] == sha(HERE / "official_q_d13_union_m10_v1.xcnf")
    assert formula["formula_bytes"] == (HERE / "official_q_d13_union_m10_v1.xcnf").stat().st_size
    assert formula["counts"] == {"variables": 337789, "clauses": 309161,
                                  "native_xors": 246591, "roots": 2489,
                                  "linear_rows": 17554}
    assert not (HERE / "build.stderr").read_text()
    assert pp["status"] == "FROZEN_BEFORE_PLANTED_CONTROL"
    assert pp["source_sha256"] == sha(HERE / "planted_control.py")
    check_inputs(pp)
    assert planted["status"] == "PASS_FULL_ASSIGNMENT"
    assert planted["protocol_sha256"] == sha(HERE / "planted_protocol.json")
    assert len(planted["leaf_codes"]) == len(planted["leaf_branch_bits"]) == 10
    assert set(planted["leaf_branch_bits"]) == {0, 1}
    assert planted["formula_counts_before_pins"]["vars"] == formula["counts"]["variables"]
    assert planted["formula_counts_before_pins"]["clauses"] == formula["counts"]["clauses"]
    assert planted["formula_counts_before_pins"]["xors"] == formula["counts"]["native_xors"]
    assert planted["checked_clause_count"] == 311661
    assert planted["checked_native_xor_count"] == 246591
    assert not (HERE / "planted.stderr").read_text()
    assert sp["status"] == "FROZEN_BEFORE_INDEPENDENT_REPLAY"
    assert sp["source_sha256"] == sha(HERE / "audit_sage.py")
    assert sp["sage_runtime_info_sha256"] == sha(HERE / "sage_runtime_info.json")
    check_inputs(sp)
    assert sage["status"] == "PASS_ALL_TEN_LEAVES_AND_TARGET_FIBER"
    assert sage["protocol_sha256"] == sha(HERE / "sage_protocol.json")
    assert (sage["checked_leaves"], sage["checked_partial_sums"],
            sage["checked_target_fiber_endpoints"]) == (10, 8, 4)
    assert not (HERE / "sage.stderr").read_text()
    print(json.dumps({"status": "PASS", "formula_counts": formula["counts"],
                      "planted": planted["status"],
                      "independent_sage": sage["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
