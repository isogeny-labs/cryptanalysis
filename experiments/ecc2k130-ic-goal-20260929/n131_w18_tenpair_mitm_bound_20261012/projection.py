"""Exact fixed-list join coverage under a uniform N131 public target."""

import hashlib
import json
import math
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
N41 = GOAL / "n41_w8_tenpair_density_control_20261012"
N131 = GOAL / "n131_w18_tenpair_binary_frob_20261012"
SUPPORT = GOAL / "n131_fixed_seed_ninepair_cubic_20261011/support_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def source_hashes():
    return {"n41_protocol": sha(N41 / "protocol.json"),
            "n41_receipt": sha(N41 / "receipt.json"),
            "n41_audit": sha(N41 / "audit_result.json"),
            "n131_protocol": sha(N131 / "protocol.json"),
            "n131_sage": sha(N131 / "sage_fixture_result.json"),
            "support": sha(SUPPORT),
            "theorem": sha(HERE / "JoinCoverage.lean"),
            "lean_check": sha(HERE / "lean_check.txt"),
            "producer": sha(Path(__file__))}


def inputs():
    n41 = load(N41 / "protocol.json")
    receipt = load(N41 / "receipt.json")
    audit = load(N41 / "audit_result.json")
    n131 = load(N131 / "protocol.json")
    support = load(SUPPORT)
    row = next(row for row in support["rows"]
               if row["label"] == "n131_w18_seed212")
    order = int(row["subgroup_order"])
    assert n41["status"] == "FROZEN_UNPINNED_N41_TENPAIR_PUBLIC_POINT_CONTROL"
    assert receipt["left_line"].startswith(f'LEFT_DONE {n41["left_kept_cap"]} ')
    assert audit["status"] == "PASS_INDEPENDENT_N41_PUBLIC_TENPAIR_RELATION"
    assert n131["curve_id"] == "EC1N131Ckb1heb5f1998f20b"
    assert n131["source_pair_slots"] == 10
    assert n131["target_choice_count"] == (
        n131["raw_preimage_count"] * n131["frobenius_rotations"])
    assert order == int(n131["labeled_mean_upper_ceiling_exact"].split("/")[1])
    return n41, receipt, n131, order


def freeze():
    n41, _, n131, order = inputs()
    check = (HERE / "lean_check.txt").read_text()
    assert "'JoinCoverage.orbit_join_coverage_bound' depends on axioms:" in check
    assert "sorryAx" not in check
    save("protocol.json", {
        "status": "FROZEN_FIXED_LIST_COVERAGE_PROJECTION",
        "curve_id": n131["curve_id"], "subgroup_order": str(order),
        "n41_left_kept_cap": n41["left_kept_cap"],
        "n41_right_kept_cap": n41["right_kept_cap"],
        "n131_tested_frobenius_rotations": n131["frobenius_rotations"],
        "raw_preimages_per_public_target": n131["raw_preimage_count"],
        "bytes_per_stored_point_example": 17,
        "table_memory_example_bytes": 4 * 1024**3,
        "probe_budget_example": n41["right_kept_cap"],
        "online_budget_example_seconds": 600,
        "input_law": "uniform public target independent of both fixed half-state lists",
        "bound": "distinct covered public targets <= rotations*left_states*right_states",
        "source_sha256": source_hashes()})


def ratio(numerator, denominator):
    value = Fraction(numerator, denominator)
    with localcontext() as context:
        context.prec = 50
        decimal = str(Decimal(value.numerator) / Decimal(value.denominator))
    return {"numerator": str(value.numerator),
            "denominator": str(value.denominator),
            "decimal": decimal}


def run():
    protocol = load(HERE / "protocol.json")
    n41, receipt, n131, order = inputs()
    assert protocol["source_sha256"] == source_hashes()
    assert protocol["subgroup_order"] == str(order)
    assert protocol["n41_left_kept_cap"] == n41["left_kept_cap"]
    assert protocol["n41_right_kept_cap"] == n41["right_kept_cap"]
    assert protocol["n131_tested_frobenius_rotations"] == n131["frobenius_rotations"]
    left = protocol["n41_left_kept_cap"]
    right = protocol["n41_right_kept_cap"]
    rotations = protocol["n131_tested_frobenius_rotations"]
    assert left == 5_000_000 and right == 5_000_000 and rotations == 131
    assert receipt["status"] == "HIT_PENDING_INDEPENDENT_REPLAY"
    pair_budget = (order + 2 * rotations - 1) // (2 * rotations)
    balanced = math.isqrt(pair_budget)
    if balanced * balanced < pair_budget:
        balanced += 1
    memory = protocol["table_memory_example_bytes"]
    bytes_per_point = protocol["bytes_per_stored_point_example"]
    optimistic_left = memory // bytes_per_point
    required_right = (pair_budget + optimistic_left - 1) // optimistic_left
    save("result.json", {
        "status": "PASS_EXACT_FIXED_LIST_N131_COVERAGE_BOUND",
        "candidate_id": None, "curve_id": protocol["curve_id"],
        "input_law": protocol["input_law"],
        "subgroup_order": str(order),
        "fixed_five_million_each": {
            "left_states": left, "right_probes": right,
            "covered_target_upper_without_orbit": str(left * right),
            "uniform_success_upper_without_orbit": ratio(left * right, order),
            "covered_target_upper_with_131_orbit": str(rotations * left * right),
            "uniform_success_upper_with_131_orbit": ratio(
                rotations * left * right, order)},
        "half_coverage_necessary": {
            "minimum_left_right_product": str(pair_budget),
            "minimum_each_when_balanced": str(balanced)},
        "compact_point_table_example": {
            "table_budget_bytes": memory,
            "bytes_per_exact_point_assumed": bytes_per_point,
            "left_states_at_budget_ignoring_overhead": optimistic_left,
            "right_probes": protocol["probe_budget_example"],
            "uniform_success_upper_with_orbit": ratio(
                rotations * optimistic_left * right, order),
            "necessary_right_probes_for_half_coverage": str(required_right),
            "necessary_right_probes_per_second_for_600s": ratio(
                required_right, protocol["online_budget_example_seconds"])},
        "four_raw_lifts_extra_factor": 1,
        "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_EXACT_FIXED_LIST_N131_COVERAGE_BOUND", flush=True)


if __name__ == "__main__":
    import sys
    {"freeze": freeze, "run": run}[sys.argv[1]]()
