"""Terminal source, arithmetic, independent-census and proof receipt audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    p, r, a, proof = (read(name) for name in
                      ("protocol.json", "result.json", "audit.json", "proof_receipt.json"))
    assert p["status"] == "FROZEN_BEFORE_FOUR_SEED_BOUND"
    assert all(sha(path) == value for path, value in p["sources"].items())
    assert r["status"] == "PASS_EXACT_FOUR_SEED_BOUND"
    assert r["protocol_sha256"] == a["protocol_sha256"] == sha(HERE / "protocol.json")
    assert a["result_sha256"] == sha(HERE / "result.json")
    assert a["status"] == "PASS_INDEPENDENT_FULL_W18_SEED_COUNT_REPLAY"
    assert a["checked_seed_counts"] == 262144
    assert r["maximum_signed_states_per_seed"] == a["maximum_signed_states_per_seed"] == 133152
    assert r["best_seed"] == a["best_seed"] == 123000
    c, n, modulus = (r["maximum_signed_states_per_seed"],
                     r["total_signed_pair_states_per_slot"], int(r["subgroup_order"]))
    assert c**4 == int(r["maximum_four_family_tuple_count"])
    assert n**4 == int(r["full_source_tuple_count"])
    q = r["half_coverage_minimum_fixed_seed_tuples"]
    assert (q-1)*2*c**4 < modulus <= q*2*c**4
    assert proof["status"] == "PASS_LEAN_4_34_1_KERNEL_CHECK"
    assert proof["source_sha256"] == sha(HERE / "FourSeedBudget.lean")
    assert proof["dependency_sha256"] == sha(HERE.parent / "n131_w18_tenpair_mitm_bound_20261012/JoinCoverage.lean")
    assert proof["dependency_log_sha256"] == sha(HERE / "lean_dependency_check.log")
    assert proof["theorem_log_sha256"] == sha(HERE / "lean_check.log")
    assert proof["exit_codes"] == [0, 0]
    lean = (HERE / "lean_check.log").read_text()
    assert "error:" not in lean and "sorryAx" not in lean
    for name in ("fixed_tuple_coverage", "fixed_schedule_coverage", "half_ceiling_is_minimal"):
        assert f"FourSeedBudget.{name}" in lean
    source = (HERE / "FourSeedBudget.lean").read_text()
    assert all(bad not in source for bad in ("sorry", "admit", "native_decide", "axiom "))
    print("PASS_FOUR_SEED_BUDGET_TERMINAL_AUDIT", c, q)


if __name__ == "__main__":
    main()
