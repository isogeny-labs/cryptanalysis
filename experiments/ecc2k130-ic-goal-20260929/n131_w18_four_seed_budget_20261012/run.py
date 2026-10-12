"""Exact target-independent four-seed coverage arithmetic from audited W18 counts."""
import hashlib
import json
import struct
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
COUNTS = GOAL / "n131_w16_w18_offset_gate_20261011/signed_w18.i64le"
SOURCE_RESULT = GOAL / "n131_w16_w18_offset_gate_20261011/result.json"
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
JOIN_PROOF = GOAL / "n131_w18_tenpair_mitm_bound_20261012/JoinCoverage.lean"
R = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def ceil_div(a, b):
    return (a + b - 1) // b


def paths():
    return [Path(__file__), HERE / "audit.py", HERE / "FourSeedBudget.lean",
            COUNTS, SOURCE_RESULT, SUPPORT, JOIN_PROOF]


def freeze():
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_FOUR_SEED_BOUND", "candidate_id": None,
        "curve_id": "EC1N131Ckb1heb5f1998f20b", "subgroup_order": str(R),
        "law": "four seed tuples chosen independently of a uniform subgroup target",
        "source": "signed distinct-column W18 pair states per seed, four rotations",
        "memory_example_bytes_per_half_state": 17,
        "sources": {str(path): sha(path) for path in paths()},
    })


def produce():
    proto = json.loads((HERE / "protocol.json").read_text())
    assert proto["status"] == "FROZEN_BEFORE_FOUR_SEED_BOUND"
    assert all(sha(path) == value for path, value in proto["sources"].items())
    start = time.monotonic_ns()
    raw = COUNTS.read_bytes()
    assert len(raw) == 262144 * 8
    counts = struct.unpack("<262144q", raw)
    assert counts[0] == 0 and all(v >= 0 and v % 4 == 0 for v in counts)
    n = sum(counts)
    prior = next(row for row in json.loads(SOURCE_RESULT.read_text())["records"]
                 if row["width"] == 18)
    assert n == prior["signed_pair_states_N"]
    assert sha(COUNTS) == prior["signed_count_sha256"]
    best_seed = max(range(1, len(counts)), key=lambda i: (counts[i], -i))
    cmax = counts[best_seed]
    tuple_cap = cmax ** 4
    half_cells = ceil_div(R, 2 * tuple_cap)
    assert (half_cells - 1) * 2 * tuple_cap < R <= half_cells * 2 * tuple_cap
    records = []
    for cells in (1, 10**3, 10**6, 10**9, 10**12):
        records.append({"fixed_seed_tuples": cells,
                        "coverage_upper_numerator": str(cells * tuple_cap),
                        "coverage_upper_denominator": str(R),
                        "minimum_enrichment_for_half": str(ceil_div(R, 2*cells*tuple_cap))})
    result = {
        "status": "PASS_EXACT_FOUR_SEED_BOUND", "candidate_id": None,
        "curve_id": proto["curve_id"], "subgroup_order": str(R),
        "total_signed_pair_states_per_slot": n,
        "nonzero_seed_count": sum(bool(v) for v in counts[1:]),
        "best_seed": best_seed, "maximum_signed_states_per_seed": cmax,
        "maximum_two_family_cross_product": cmax * cmax,
        "maximum_four_family_tuple_count": str(tuple_cap),
        "half_coverage_minimum_fixed_seed_tuples": half_cells,
        "full_source_tuple_count": str(n ** 4),
        "full_source_mean_numerator": str(n ** 4),
        "full_source_mean_denominator": str(R),
        "illustrative_half_list_bytes_at_17_per_state": str(17*cmax*cmax),
        "six_hundred_second_minimum_tuple_tests_per_second": ceil_div(half_cells, 600),
        "schedule_rows": records, "elapsed_ns": time.monotonic_ns() - start,
        "protocol_sha256": sha(HERE / "protocol.json"),
    }
    save(HERE / "result.json", result)
    print(json.dumps({k: result[k] for k in
                      ("status", "best_seed", "maximum_signed_states_per_seed",
                       "half_coverage_minimum_fixed_seed_tuples")}, sort_keys=True))


if __name__ == "__main__":
    {"freeze": freeze, "produce": produce}[sys.argv[1]]()
