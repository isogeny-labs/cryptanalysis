"""Exact source-count and conditional uniform-residual work projection."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
N41_ORDER = 549756390943
N131_ORDER = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    receipt = json.loads((HERE / "result.json").read_text())
    assert receipt["protocol_sha256"] == sha(HERE / "protocol.json")
    assert receipt["status"] in ("EXHAUSTED", "HIT_PENDING_INDEPENDENT_REPLAY")
    counts = Counter()
    masks = set()
    for line in SUPPORT.read_text().splitlines():
        mask, column = map(int, line.split())
        assert mask not in masks
        masks.add(mask)
        counts[column] += 1
    M = len(masks)
    assert (M, len(counts)) == (131307, 131068)
    S = 4 * (M * (M - 1) // 2 - sum(m * (m - 1) // 2 for m in counts.values()))
    assert S == 34482792912
    pair_output_probability_bound = Fraction(S, N131_ORDER)
    probe_count = protocol["kept_limit"]
    projection = {"status": "PASS_EXACT_SOURCE_UNIFORM_RESIDUAL_PROJECTION",
                  "candidate_id": None, "n41_query_status": receipt["status"],
                  "n41_source_state_count": 30952,
                  "n41_uniform_single_probe_upper_bound": str(Fraction(30952, N41_ORDER)),
                  "n131_support_sha256": sha(SUPPORT),
                  "n131_source_masks": M, "n131_folded_columns": len(counts),
                  "n131_signed_pair_states": S,
                  "n131_uniform_single_probe_upper_bound": str(pair_output_probability_bound),
                  "n131_uniform_expected_hits_at_frozen_kept_limit": str(probe_count * pair_output_probability_bound),
                  "n131_uniform_probes_for_expected_one_hit_lower_bound": str(Fraction(N131_ORDER, S)),
                  "projection_assumption": "Each target-derived residual is independently uniform on the prime-order subgroup; source-output multiplicity only lowers the hit probability relative to the state-count bound.",
                  "scope": "Arithmetic upper bound under a conditional uniform model; no lower bound on a nonuniform target-coupled generator and no runtime complexity claim.",
                  "protocol_sha256": sha(HERE / "protocol.json"),
                  "query_result_sha256": sha(HERE / "result.json")}
    with (HERE / "projection.json").open("x") as out:
        json.dump(projection, out, sort_keys=True, indent=2)
        out.write("\n")
    print(projection["status"], projection["n131_uniform_probes_for_expected_one_hit_lower_bound"])


if __name__ == "__main__":
    main()
