"""Read-only independent integer replay of the fixed-list coverage row."""

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def main():
    protocol = load(HERE / "protocol.json")
    result = load(HERE / "result.json")
    paths = {
        "n41_protocol": GOAL / "n41_w8_tenpair_density_control_20261012/protocol.json",
        "n41_receipt": GOAL / "n41_w8_tenpair_density_control_20261012/receipt.json",
        "n41_audit": GOAL / "n41_w8_tenpair_density_control_20261012/audit_result.json",
        "n131_protocol": GOAL / "n131_w18_tenpair_binary_frob_20261012/protocol.json",
        "n131_sage": GOAL / "n131_w18_tenpair_binary_frob_20261012/sage_fixture_result.json",
        "support": GOAL / "n131_fixed_seed_ninepair_cubic_20261011/support_result.json",
        "theorem": HERE / "JoinCoverage.lean",
        "lean_check": HERE / "lean_check.txt",
        "producer": HERE / "projection.py",
    }
    assert protocol["source_sha256"] == {key: sha(path) for key, path in paths.items()}
    assert result["status"] == "PASS_EXACT_FIXED_LIST_N131_COVERAGE_BOUND"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    n41, n131, support = (load(paths[key]) for key in
                           ("n41_protocol", "n131_protocol", "support"))
    n131_row = next(row for row in support["rows"]
                    if row["label"] == "n131_w18_seed212")
    order = int(n131_row["subgroup_order"])
    left = int(n41["left_kept_cap"])
    right = int(n41["right_kept_cap"])
    rotations = int(n131["frobenius_rotations"])
    assert result["subgroup_order"] == protocol["subgroup_order"] == str(order)
    assert result["curve_id"] == n131["curve_id"]
    assert result["fixed_five_million_each"]["left_states"] == left
    assert result["fixed_five_million_each"]["right_probes"] == right
    rows = result["fixed_five_million_each"]
    assert int(rows["covered_target_upper_without_orbit"]) == left * right
    assert int(rows["covered_target_upper_with_131_orbit"]) == rotations * left * right
    for name, numerator in (("uniform_success_upper_without_orbit", left * right),
                            ("uniform_success_upper_with_131_orbit", rotations * left * right)):
        # The order is prime and these small products are coprime to it.
        assert (int(rows[name]["numerator"]), int(rows[name]["denominator"])) == (
            numerator, order)
    product = (order + 2 * rotations - 1) // (2 * rotations)
    threshold = math.isqrt(product)
    threshold += int(threshold * threshold < product)
    assert int(result["half_coverage_necessary"]["minimum_left_right_product"]) == product
    assert int(result["half_coverage_necessary"]["minimum_each_when_balanced"]) == threshold
    table = result["compact_point_table_example"]
    cap = int(table["table_budget_bytes"]) // int(table["bytes_per_exact_point_assumed"])
    assert cap == table["left_states_at_budget_ignoring_overhead"]
    assert int(table["uniform_success_upper_with_orbit"]["numerator"]) == rotations * cap * right
    assert int(table["uniform_success_upper_with_orbit"]["denominator"]) == order
    probes = (product + cap - 1) // cap
    assert int(table["necessary_right_probes_for_half_coverage"]) == probes
    assert result["four_raw_lifts_extra_factor"] == 1
    assert "sorryAx" not in (HERE / "lean_check.txt").read_text()
    print("PASS_EXACT_FIXED_LIST_COVERAGE_REPLAY", flush=True)


if __name__ == "__main__":
    main()
