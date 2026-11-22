"""Terminal audit of the fixed-outer support census and coverage arithmetic."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


protocol = read(HERE / "verification_protocol.json")
assert protocol["status"] == "FROZEN_BEFORE_TERMINAL_AUDIT"
for name, record in protocol["sources"].items():
    assert digest(record["path"]) == record["sha256"], name

producer = read(HERE / "run_v2_result.json")
sorter = read(HERE / "audit_result.json")
attempt = read(HERE / "attempt1.json")
bound = read(HERE / "bound_result.json")
prior_audit = read(protocol["sources"]["prior_relation_audit"]["path"])
prior_lean = Path(protocol["sources"]["prior_lean_receipt"]["path"]).read_text()

assert attempt["status"] == "SUPERVISOR_FAILURE_BEFORE_WORKER_START"
assert attempt["worker_started"] is False
assert producer["status"] == "COMPLETE_N41_RIGHT_SUPPORT"
assert sorter["status"] == "PASS_SORTED_N41_RIGHT_SUPPORT_AUDIT"
assert producer["exit_code"] == sorter["exit_code"] == 0
assert producer["peak_child_rss_raw"] < producer["rss_cap_bytes"]
assert sorter["peak_child_rss_raw"] < 1 << 32
for key, value in {"states_per_slot":1124,"addition_checks":128,
                   "compatible_pairs":1258720,"rejected_pairs":4656,
                   "distinct_sums":1258720,"duplicate_pairs":0}.items():
    assert producer["row"][key] == sorter["row"][key] == value, key
assert producer["row"]["compatible_pairs"] + producer["row"]["rejected_pairs"] == 1124**2
assert prior_audit["status"] == "PASS_INDEPENDENT_N41_W11_FIVEPAIR_PUBLIC_RELATION"
assert prior_audit["raw_group_sum_matches_target"] is True
assert prior_audit["projected_subgroup_sum_matches_target"] is True
assert "'AdviceBound.successful_targets_le' depends on axioms: [propext, Classical.choice, Quot.sound]" in prior_lean

n41 = bound["n41"]
n131 = bound["n131"]
assert bound["status"] == "PASS_W29_FIXED_OUTER_COVERAGE_BOUND"
assert bound["candidate_id"] is None
assert n41["distinct_right_pair_sums"] == 1258720
assert n41["raw_group_order"] == 4 * 549756390943
assert n131["subgroup_order"] == 680564733841876926932320129493409985129
assert n131["raw_code_capacity"] == 1 << 28
assert n131["signed_state_ceiling"] == 4 * (1 << 28)
assert n131["ordered_right_pair_sum_ceiling"] == (4 * (1 << 28))**2
assert n131["sample_projected_valid_codes"] == 16677 * (1 << 28) // 65536
assert n131["sample_projected_ordered_pair_ceiling"] == (4 * n131["sample_projected_valid_codes"])**2
for label, m in [("advice_panels_max_source", n131["ordered_right_pair_sum_ceiling"]),
                 ("advice_panels_sample_projection", n131["sample_projected_ordered_pair_ceiling"])]:
    for panel in n131[label]:
        k = panel["fixed_proposals_per_advice"]
        r = n131["subgroup_order"]
        bits = panel["minimum_advice_bits_for_half_bound"]
        assert panel["minimum_advice_values_for_half_bound"] == (r + 2*k*m - 1) // (2*k*m)
        assert 2 * (1 << (bits-1)) * k * m < r
        assert 2 * (1 << bits) * k * m >= r
        assert panel["upper_at_preceding_bit_count_numerator"] == min(r,(1 << (bits-1))*k*m)
        assert panel["upper_at_threshold_bit_count_numerator"] == min(r,(1 << bits)*k*m)
assert [(p["fixed_proposals_per_advice"],p["minimum_advice_bits_for_half_bound"])
        for p in n131["advice_panels_max_source"]] == [(1,69),(20000000,44),(600000000000,29)]
assert [(p["fixed_proposals_per_advice"],p["minimum_advice_bits_for_half_bound"])
        for p in n131["advice_panels_sample_projection"]] == [(1,72),(20000000,48),(600000000000,33)]

lean = Path(HERE / "lean.stdout").read_text()
assert Path(HERE / "lean.stderr").read_text() == ""
names = ["sixtyEightBitsInsufficient", "sixtyNineBitsCrossArithmeticThreshold",
         "fortyThreeBitsInsufficient", "fortyFourBitsCrossArithmeticThreshold",
         "twentyEightBitsInsufficient", "twentyNineBitsCrossArithmeticThreshold",
         "projectedFortySevenBitsInsufficient", "projectedFortyEightBitsCrossArithmeticThreshold",
         "projectedSeventyOneBitsInsufficient", "projectedSeventyTwoBitsCrossArithmeticThreshold",
         "projectedThirtyTwoBitsInsufficient", "projectedThirtyThreeBitsCrossArithmeticThreshold"]
assert lean.count("does not depend on any axioms") == len(names)
for name in names:
    assert f"'W29AdviceThreshold.{name}' does not depend on any axioms" in lean
assert "sorry" not in Path(HERE / "W29AdviceThreshold.lean").read_text()

result = {"status":"PASS_TERMINAL_AUDIT", "candidate_id":None,
          "protocol_sha256":digest(HERE / "verification_protocol.json"),
          "verifier_sha256":digest(__file__),
          "n41_distinct_right_sums":1258720,
          "w29_rigorous_threshold_bits":[69,44,29],
          "w29_projected_threshold_bits":[72,48,33],
          "lean_theorems_checked":len(names),
          "prior_structural_theorem_checked":"AdviceBound.successful_targets_le"}
(HERE / "verification_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True))
