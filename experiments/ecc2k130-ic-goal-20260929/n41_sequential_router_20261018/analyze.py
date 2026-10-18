"""Exact sequential router synthesis on the frozen N41 target/source rows."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "n41_product_mask_interpolation_20261015"))
sys.path.insert(0, str(ROOT / "n41_router_degree6_coefficients_20261015"))
import interpolate
import synthesize
import trace_synthesize

protocol = json.loads((HERE / "protocol.json").read_text())
for relative, expected in protocol["sources_sha256"].items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == protocol["script_sha256"]

base = json.loads((ROOT / "n41_router_degree6_coefficients_20261015" /
                   "trace_result.json").read_text())
frozen = json.loads((ROOT / "n41_router_degree6_coefficients_20261015" /
                     "trace_protocol.json").read_text())
assert base["status"] == "PASS_TARGET_TRACE_ROUTER_INTERPOLATION"
assert frozen["target"] == protocol["target"]
assert frozen["selected_features"] == protocol["selected_features"]
assert base["trace_compatible_cases"] == 766

started = time.monotonic()
geometry = json.loads(synthesize.GEOMETRY.read_text())
code_masks = [[block["states"][4*code]["a"] for code in range(40)]
              for block in geometry["blocks"][:2]]
cases = [json.loads(line) for line in synthesize.CASES.read_text().splitlines()]
feature_pairs = [synthesize.pair_from_bit(bit)
                 for bit in protocol["selected_features"]]
monomials, prefix = interpolate.monomials()
positions = {mask: index for index, mask in enumerate(monomials)}
rows = []
for index, case in enumerate(cases):
    if (case["x_coordinates"][0] & 1) != (protocol["target"] & 1):
        continue
    bits = code_masks[0][case["left_code"]] | (code_masks[1][case["right_code"]] << 8)
    feature = interpolate.feature(bits, positions)
    label = 0
    for k, (i, j) in enumerate(feature_pairs):
        label |= int(all(not ((x >> i & 1) & (x >> j & 1))
                         for x in case["x_coordinates"])) << k
    rows.append((index, feature, label))
assert len(rows) == 766
assert [index for index, _, _ in rows] == base["trace_compatible_source_indices"]

active = rows
remaining = list(range(len(feature_pairs)))
stages = []
for stage in range(protocol["max_selected_gates"] + 1):
    remaining_mask = sum(1 << bit for bit in remaining)
    rank_rows = []
    first_fitting = None
    first_full = None
    for degree, count in enumerate(prefix):
        rank, inconsistent = interpolate.high_pivot_rank(
            [(feature, label & remaining_mask) for _, feature, label in active], count)
        fitting = remaining_mask & ~inconsistent
        rank_rows.append({"degree": degree, "monomials": count,
                          "rank": rank, "fitting_remaining": fitting.bit_count(),
                          "remaining": len(remaining)})
        if first_fitting is None and fitting == remaining_mask:
            first_fitting = degree
        if first_full is None and rank == len(active):
            first_full = degree
        if first_fitting is not None and first_full is not None:
            break
    assert first_fitting is not None and first_full is not None
    count = prefix[first_full]
    reduced = [(feature & ((1 << count)-1), label & remaining_mask)
               for _, feature, label in active]
    variants = {}
    for direction in ("high", "low"):
        masks, rank = trace_synthesize.solve(reduced, monomials[:count], direction)
        assert rank == len(active)
        predicates = []
        for bit in remaining:
            mask = masks[bit]
            positions_list = [pos for pos in range(count) if mask >> pos & 1]
            assert all(((feature & mask).bit_count() & 1) == (label >> bit & 1)
                       for _, feature, label in active)
            predicates.append({"feature_bit": protocol["selected_features"][bit],
                               "gate_index": bit,
                               "coefficient_positions": positions_list,
                               "monomial_count": len(positions_list),
                               "separated_matrix_rank": synthesize.matrix_rank(mask, monomials[:count])})
        variants[direction] = {"total_monomial_occurrences":
                               sum(p["monomial_count"] for p in predicates),
                               "total_separated_rank":
                               sum(p["separated_matrix_rank"] for p in predicates),
                               "predicates": predicates}
    step = {"stage": stage, "surviving_source_indices": [index for index, _, _ in active],
            "survivor_count": len(active), "remaining_gate_count": len(remaining),
            "degree_ranks": rank_rows, "first_fitting_degree": first_fitting,
            "first_full_rank_degree": first_full, "variants": variants}
    if stage == protocol["max_selected_gates"]:
        stages.append(step)
        break
    scores = [(sum((label >> bit) & 1 for _, _, label in active), -bit, bit)
              for bit in remaining]
    rejected, _, chosen = max(scores)
    assert rejected > 0
    step["selected_gate_index"] = chosen
    step["selected_feature_bit"] = protocol["selected_features"][chosen]
    step["rejected_family_count"] = rejected
    next_active = [row for row in active if not (row[2] >> chosen & 1)]
    assert len(next_active) == len(active) - rejected
    stages.append(step)
    active = next_active
    remaining.remove(chosen)

elapsed = time.monotonic() - started
assert elapsed < protocol["wall_cap_seconds"]
peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
assert peak_rss < protocol["rss_cap_bytes"]
out = {"status": "COMPLETE_SEQUENTIAL_ROUTER_SYNTHESIS",
       "candidate_id": None, "curve_id": protocol["curve_id"],
       "target": protocol["target"], "stages": stages,
       "wall_seconds_exploratory": elapsed, "peak_self_rss_bytes": peak_rss,
       "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()}
(HERE / "result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": out["status"], "wall_seconds": elapsed,
                  "stages": [(s["survivor_count"], s["remaining_gate_count"],
                              s["first_fitting_degree"],s["first_full_rank_degree"],
                              s.get("selected_gate_index")) for s in stages]},
                 sort_keys=True))
