"""Exact source size and conditional uniform-triple occupancy projection."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
ORDER = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    q = json.loads((HERE / "result.json").read_text())
    assert q["protocol_sha256"] == sha(HERE / "protocol.json")
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
    literal_index_entries = S * (S - 1) // 2
    triple_occupancy_bound = Fraction(S**3, ORDER)
    result = {"status": "PASS_EXACT_N131_TRIPLE_SOURCE_PROJECTION",
              "candidate_id": None, "n41_query_status": q["status"],
              "n41_source_states": 1956,
              "n41_index_entries": int(q["index_line"].split()[1]),
              "n131_support_sha256": sha(SUPPORT),
              "n131_source_masks": M, "n131_folded_columns": len(counts),
              "n131_signed_pair_states": S,
              "n131_literal_unordered_two_pair_index_entries": str(literal_index_entries),
              "n131_uniform_triple_completion_probability_upper_bound": str(triple_occupancy_bound),
              "n131_uniform_outer_families_for_expected_one_hit_lower_bound": str(Fraction(ORDER, S**3)),
              "n131_literal_one_byte_per_index_entry": str(literal_index_entries),
              "scope": "The occupancy bound assumes a uniform target-derived residual for each outer family. It does not bound an adaptive nonuniform generator. The literal index size is a direct materialization cost, not an information-theoretic lower bound.",
              "protocol_sha256": sha(HERE / "protocol.json"),
              "query_result_sha256": sha(HERE / "result.json")}
    with (HERE / "projection.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result["status"], result["n131_uniform_outer_families_for_expected_one_hit_lower_bound"])


if __name__ == "__main__":
    main()
