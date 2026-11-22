"""Freeze four signs of one W18 terminal edge and count source support."""

import hashlib
import importlib.util
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
VERIFY = ROOT / "n131_fixed_seed_halftrace_cubic_20261011"
sys.path.insert(0, str(BASE))
import run as base  # noqa: E402
support_spec = importlib.util.spec_from_file_location("ninepair_support", BASE / "support.py")
support = importlib.util.module_from_spec(support_spec)
support_spec.loader.exec_module(support)
sys.path.insert(0, str(VERIFY))
import verify as independent  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def neg(point):
    x, y = point
    return x, y ^ x


def subtract(left, right):
    return independent.point_add(tuple(left), neg(tuple(right)))


def pool_states():
    columns = support.columns_from(base.SUPPORT)
    codes = sorted(base.pair.valid_codes(columns))
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    control_code = base.pair.selector_code(fixture["selected"][8]["masks"][0])
    chosen = [control_code]
    assert len(chosen) == 1
    states = []
    for code in chosen:
        a = base.pair.mask_from_code(code)
        b = a ^ base.pair.SEED
        assert a in columns and b in columns and columns[a] != columns[b]
        for sign_a in range(2):
            for sign_b in range(2):
                raw = independent.point_add(independent.point_options(a)[sign_a],
                                            independent.point_options(b)[sign_b])
                assert raw is not None and raw[0] not in (0, 1)
                rotated = tuple(independent.frobenius(v, 128) for v in raw)
                assert rotated[0] not in (0, 1)
                states.append({"code": code, "masks": [a, b],
                               "folded_columns": [columns[a], columns[b]],
                               "signs": [sign_a, sign_b],
                               "rotated_raw_point": list(rotated)})
    assert len(states) == 4
    assert len({tuple(row["rotated_raw_point"]) for row in states}) == 4
    old_target = json.loads((base.OLD / "planted_chain_result.json").read_text())["raw_target"]
    expected = subtract(fixture["raw_target"], old_target)
    matches = [index for index, row in enumerate(states)
               if tuple(row["rotated_raw_point"]) == expected]
    assert len(matches) == 1
    assert states[matches[0]]["code"] == control_code
    return states, matches[0], columns


def source_ceiling(states, columns):
    edges = [(columns[a], columns[a ^ base.pair.SEED])
             for a in columns if a < (a ^ base.pair.SEED)
             and a ^ base.pair.SEED in columns
             and columns[a] != columns[a ^ base.pair.SEED]]
    assert len(edges) == 33191
    by_edge = {}
    for row in states:
        edge = tuple(row["folded_columns"])
        if edge in by_edge:
            continue
        occupied = set(edge)
        remaining = [candidate for candidate in edges
                     if not occupied.intersection(candidate)]
        coefficients, _, _ = support.matching_counts(remaining, cap=8)
        by_edge[edge] = {"remaining_edges": len(remaining),
                         "eight_pair_matchings": coefficients[8]}
    assert len(by_edge) == 1
    multiplier = math.factorial(8) * 4**8
    count = sum(by_edge[tuple(row["folded_columns"])]["eight_pair_matchings"]
                * multiplier for row in states)
    full_curve_order = 4 * support.R131
    mean = Fraction(count, full_curve_order)
    return {"status": "PASS_EXACT_SELECTED_TERMINAL_SOURCE_COUNT",
            "selected_signed_states": len(states),
            "selected_pair_edges": len(by_edge),
            "remaining_pair_slots": 8,
            "eligible_unordered_source_edges": len(edges),
            "conditional_edge_rows": [
                {"folded_columns": list(edge), **data}
                for edge, data in sorted(by_edge.items())],
            "signed_ordered_distinct_column_tuples": str(count),
            "uniform_raw_point_mean_upper_exact": f"{mean.numerator}/{mean.denominator}",
            "uniform_raw_point_mean_upper_decimal": format(float(mean), ".12g"),
            "full_curve_order": str(full_curve_order),
            "source_sha256": {"script": sha(Path(__file__)),
                              "support": sha(base.SUPPORT),
                              "matching_counter": sha(BASE / "support.py")}}


def main():
    states, control_index, columns = pool_states()
    source = source_ceiling(states, columns)
    save("pool.json", {"status": "PASS_FROZEN_TARGET_INDEPENDENT_TERMINAL_POOL",
                       "curve_id": "EC1N131Ckb1heb5f1998f20b",
                       "seed_mask": base.pair.SEED, "rotation": 128,
                       "selection_law": "constructed-control edge fixed before the public query; all four sign choices for that single edge",
                       "control_choice_index": control_index,
                       "states": states,
                       "source_sha256": {"script": sha(Path(__file__)),
                                         "fixture": sha(BASE / "control_fixture.json"),
                                         "support": sha(base.SUPPORT),
                                         "independent_group": sha(VERIFY / "verify.py")}})
    save("source_count.json", source)
    print(json.dumps({"status": source["status"],
                      "states": len(states),
                      "uniform_mean_upper": source["uniform_raw_point_mean_upper_decimal"]}),
          flush=True)


if __name__ == "__main__":
    main()
