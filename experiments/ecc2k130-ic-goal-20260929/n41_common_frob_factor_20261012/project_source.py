"""Exact N131 five-pair distinct-column source lower bound and fixed-list gate."""

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
ORDER = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "source_projection_protocol.json").read_text())
    files = {"runner": HERE / "project_source.py", "support": SUPPORT,
             "n41_audit": HERE / "audit_result.json",
             "n131_target": HERE / "n131_projection_result.json"}
    assert protocol["status"] == "FROZEN_BEFORE_N131_SOURCE_COUNT"
    assert protocol["sha256"] == {name: sha(path) for name, path in files.items()}
    counts = Counter()
    masks = set()
    for line in SUPPORT.read_text().splitlines():
        mask, column = map(int, line.split())
        assert mask not in masks
        masks.add(mask)
        counts[column] += 1
    M = len(masks)
    assert M == 131307 and len(counts) == 131068
    pair_states = 4*(M*(M-1)//2-sum(m*(m-1)//2 for m in counts.values()))
    assert pair_states == 34482792912
    max_incident = max(4*m*(M-m) for m in counts.values())
    assert max_incident == 2100848
    factors = [pair_states-2*j*max_incident for j in range(5)]
    assert min(factors) > 0
    lower = 1
    for factor in factors:
        lower *= factor
    assert lower > ORDER
    n41 = json.loads((HERE / "audit_result.json").read_text())
    n131 = json.loads((HERE / "n131_projection_result.json").read_text())
    assert n41["rank_after"] == 7
    assert n131["status"] == "PASS_CHECKED_SAGE_N131_COMMON_FACTOR_TARGET"
    assert n131["frobenius_shift"] == 16
    assert n131["factor_mod_r"]*n131["inverse_mod_r"] % ORDER == 1
    fixed_list_product = 2000000*5000000
    result = {"status": "PASS_N131_FIVEPAIR_SOURCE_LOWER_BOUND",
              "curve_id": n131["curve_id"], "candidate_id": None,
              "source_masks": M, "folded_columns": len(counts),
              "max_masks_per_column": max(counts.values()),
              "signed_pair_states": pair_states,
              "max_signed_states_incident_to_one_column": max_incident,
              "sequential_lower_factors": [str(x) for x in factors],
              "ordered_fivepair_distinct_column_lower_bound": str(lower),
              "uniform_target_mean_lower_bound_numerator": str(lower),
              "uniform_target_mean_lower_bound_denominator": str(ORDER),
              "fixed_list_2m_by_5m_uniform_hit_numerator": str(fixed_list_product),
              "fixed_list_2m_by_5m_uniform_hit_denominator": str(ORDER),
              "public_point": n131["public_point"],
              "transformed_target": n131["transformed_target"],
              "target_raw_preimage_count": len(n131["raw_preimages"]),
              "protocol_sha256": sha(HERE / "source_projection_protocol.json")}
    with (HERE / "source_projection_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result["status"], pair_states, lower, flush=True)


if __name__ == "__main__":
    main()
