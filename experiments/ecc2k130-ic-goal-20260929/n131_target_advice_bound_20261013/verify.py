"""Read-only exact-integer and proof-receipt audit."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    r = json.loads((HERE / "count_result.json").read_text())
    paths = {"script": HERE / "count.py", "lean_theorem": HERE / "AdviceBound.lean",
             "lean_toolchain": HERE / "lean-toolchain",
             "prior_count": GOAL / "n131_target_independent_completion_bound_20261013/count_result.json",
             "source": GOAL / "n41_common_frob_factor_20261012/source_projection_result.json"}
    assert {key: sha(path) for key, path in paths.items()} == p["sha256"]
    prior = json.loads(paths["prior_count"].read_text())
    source = json.loads(paths["source"].read_text())
    S = int(source["signed_pair_states"])
    M = S * (S - 1) // 2
    order = int(prior["subgroup_order"])
    assert r["protocol_sha256"] == sha(HERE / "protocol.json")
    assert r["signed_pair_states"] == S and int(r["two_pair_completion_ceiling"]) == M
    assert int(r["subgroup_order"]) == order
    for k in p["proposal_budgets"]:
        row = r["budgets"][str(k)]
        C = (order + 2 * k * M - 1) // (2 * k * M)
        bits = (C - 1).bit_length()
        assert int(row["minimum_advice_values_for_half_bound"]) == C
        assert row["minimum_advice_bits_for_half_bound"] == bits
        for b in p["advice_bit_panels"]:
            item = row["advice_bit_panels"][str(b)]
            assert int(item["probability_upper_numerator"]) == min(order, (1 << b) * k * M)
            assert int(item["probability_upper_denominator"]) == order
    proof = (HERE / "lean_check.txt").read_text()
    assert "error:" not in proof and "sorryAx" not in proof
    assert "AdviceBound.successful_targets_le" in proof
    assert (HERE / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1"
    preproof = json.loads((HERE / "protocol_preproof.json").read_text())
    early = json.loads((HERE / "count_preproof.json").read_text())
    assert preproof["sha256"]["lean_theorem"] == sha(HERE / "AdviceBound_preproof.lean")
    assert early["protocol_sha256"] == sha(HERE / "protocol_preproof.json")
    for k in p["proposal_budgets"]:
        assert early["budgets"][str(k)] == r["budgets"][str(k)]
    print(json.dumps({"status": "PASS_EXACT_ADVICE_COUNT_AND_PROOF_RECEIPT",
                      "proposal_budgets": p["proposal_budgets"],
                      "required_bits": {str(k): r["budgets"][str(k)]["minimum_advice_bits_for_half_bound"]
                                        for k in p["proposal_budgets"]}}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
