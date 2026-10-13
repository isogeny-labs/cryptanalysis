"""Exact N131 advice-alphabet lower bounds for fixed proposal budgets."""
from decimal import Decimal, localcontext
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PRIOR = GOAL / "n131_target_independent_completion_bound_20261013/count_result.json"
SOURCE = GOAL / "n41_common_frob_factor_20261012/source_projection_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ceil_div(a, b):
    return (a + b - 1) // b


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    files = {"script": HERE / "count.py", "lean_theorem": HERE / "AdviceBound.lean",
             "lean_toolchain": HERE / "lean-toolchain", "prior_count": PRIOR,
             "source": SOURCE}
    assert {key: sha(path) for key, path in files.items()} == protocol["sha256"]
    prior = json.loads(PRIOR.read_text())
    source = json.loads(SOURCE.read_text())
    S = int(source["signed_pair_states"])
    M = S * (S - 1) // 2
    r = int(prior["subgroup_order"])
    assert M == int(prior["unordered_two_pair_ceiling"])
    assert r == int(source["uniform_target_mean_lower_bound_denominator"])
    budgets = {}
    with localcontext() as ctx:
        ctx.prec = 35
        for k in protocol["proposal_budgets"]:
            C = ceil_div(r, 2 * k * M)
            bits = (C - 1).bit_length()
            assert (1 << bits) >= C and (bits == 0 or 1 << (bits - 1) < C)
            rows = {}
            for b in protocol["advice_bit_panels"]:
                num = min(r, (1 << b) * k * M)
                rows[str(b)] = {"probability_upper_numerator": str(num),
                                "probability_upper_denominator": str(r),
                                "decimal_upper": str(Decimal(num) / Decimal(r))}
            budgets[str(k)] = {"minimum_advice_values_for_half_bound": str(C),
                               "minimum_advice_bits_for_half_bound": bits,
                               "advice_bit_panels": rows}
    result = {"status": "PASS_EXACT_N131_TARGET_ADVICE_BOUND",
              "candidate_id": None, "curve_id": prior["curve_id"],
              "input_law": protocol["input_law"], "signed_pair_states": S,
              "two_pair_completion_ceiling": str(M), "subgroup_order": str(r),
              "budgets": budgets, "protocol_sha256": sha(HERE / "protocol.json")}
    path = HERE / "count_result.json"
    assert not path.exists()
    path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: {"min_values": v["minimum_advice_values_for_half_bound"],
                          "min_bits": v["minimum_advice_bits_for_half_bound"]}
                      for k, v in budgets.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
