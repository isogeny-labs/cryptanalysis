#!/usr/bin/env python3
"""The AGENTS.md section 5a band from counted native work.

For every arm, the priced cost of one solved target is

    cost(w) = group operations + w * (unpriced native operations),  w in {0, 0.1, 1}

in group-addition equivalents (GAE), with the same kind map applied to every
arm (`CLASSES`). Each arm is compared with the matched rho (`--reference`,
same points) and two arms are ranked only where their order holds at every
weight of the band and at both ends of every bound below. Otherwise the pair
is reported as unresolved at that boundary, never as a win for either side.

Input (`--input`, schema `ic-band-input/v1`):

    {"schema": "ic-band-input/v1", "r_bits": 53, "reference": "rT",
     "arms": {"S": {"family": "ic", "units": {"s000": {"ec_add": 12, ...}, ...}},
              "rT": {"family": "rho", "units": {"s000": {"group_additions": ...}}}}}

A unit is one solved target with all of its arm's work (for an IC arm: its
rank stage plus setup, linear algebra and the target's online interval; for
rho: setup and solve). Only points present in every arm are used, so every
comparison is paired.

Kind map. `ic` (the counted producer's `op_counts` kinds): group = `ec_add`
+ `ec_double`; unpriced native = every `native` and `endomorphism` kind and
`ec_add_trivial`; reported but not priced (already inside a priced kind):
`ec_scalar_mul` (its doublings and additions are counted), `la_row_eliminations`
(a grouping of `la_mulmods`) and the `field_*` kinds (inside group operations
and root solves). `rho` (the tuned rho's `charges_setup_and_solve`): group =
`group_additions`; unpriced native = `canonicalizations`, `partition_hashes`,
`table_queries`, `table_inserts`, `failed_collisions`. The tuned rho does not
decompose its `scalar_multiplications` (jumps, walk starts, candidate checks)
into group operations, so they are a bound: each costs between 0 and
2 (r_bits - 1) GAE (double-and-add of a scalar below r), and every verdict
must hold at both ends. Frobenius applications are listed as group-operation
kinds by the producer but priced here as native work, like the rho's orbit
canonicalizations; `--frobenius-as-group` prices them at 1 GAE instead, as a
sensitivity read-out.

Uncertainty: the paired bootstrap over points (`--draws`, seed fixed) of the
ratio of mean costs; a ranking also needs the 95% interval of that ratio to
exclude 1 at every band point.
"""

import argparse
import json
import random
import sys
from pathlib import Path

WEIGHTS = (0.0, 0.1, 1.0)
CLASSES = {
    "ic": {
        "group": ("ec_add", "ec_double"),
        "unpriced": ("ec_add_trivial", "frobenius_x", "fold_rotations", "ec_frobenius", "s3_root_solves",
                     "s3_root_solves_library", "canonicalizations", "root_index_probes", "root_index_inserts",
                     "root_filter_queries", "root_filter_inserts", "relation_lifts", "ec_lift_x", "la_mulmods",
                     "la_inversions", "descent_mulmods"),
        "reported": ("ec_scalar_mul", "la_row_eliminations", "field_mul", "field_sqr", "field_inv",
                     "field_half_trace"),
        "bounded": (),
    },
    "rho": {
        "group": ("group_additions",),
        "unpriced": ("canonicalizations", "partition_hashes", "table_queries", "table_inserts",
                     "failed_collisions"),
        "reported": (),
        "bounded": ("scalar_multiplications",),
    },
}
FROBENIUS = ("frobenius_x", "fold_rotations", "ec_frobenius")


def classes(family, frobenius_as_group):
    spec = {key: tuple(value) for key, value in CLASSES[family].items()}
    if frobenius_as_group and family == "ic":
        spec["group"] = spec["group"] + FROBENIUS
        spec["unpriced"] = tuple(kind for kind in spec["unpriced"] if kind not in FROBENIUS)
    return spec


def split_unit(unit, spec, family):
    known = set(spec["group"]) | set(spec["unpriced"]) | set(spec["reported"]) | set(spec["bounded"])
    unknown = sorted(set(unit) - known)
    if unknown:
        raise ValueError("%s unit has kinds the map does not classify: %s" % (family, ", ".join(unknown)))
    missing = sorted(kind for kind in set(spec["group"]) | set(spec["unpriced"]) | set(spec["bounded"])
                     if kind not in unit)
    if missing:
        raise ValueError("%s unit does not emit %s: it cannot be ranked (section 5a)" % (family, ", ".join(missing)))
    return (sum(unit[k] for k in spec["group"]), sum(unit[k] for k in spec["unpriced"]),
            sum(unit[k] for k in spec["bounded"]))


def cost(parts, weight, bound_gae):
    group, unpriced, bounded = parts
    return group + bounded * bound_gae + weight * unpriced


def mean(values):
    return sum(values) / len(values)


def analyse(data, draws=10000, seed=20261023, frobenius_as_group=False):
    reference = data["reference"]
    r_bits = int(data["r_bits"])
    bound_ends = (0.0, 2.0 * (r_bits - 1))
    arms = data["arms"]
    points = sorted(set.intersection(*(set(arm["units"]) for arm in arms.values())))
    if not points:
        raise ValueError("no point is common to every arm")
    parts = {}
    for name, arm in arms.items():
        spec = classes(arm["family"], frobenius_as_group)
        parts[name] = {point: split_unit(arm["units"][point], spec, arm["family"]) for point in points}
    grid = [(w, b) for w in WEIGHTS for b in bound_ends]
    rng = random.Random(seed)
    resamples = [[rng.randrange(len(points)) for _ in points] for _ in range(draws)] if len(points) > 1 else []

    def arm_cost(name, w, b, sample=None):
        chosen = points if sample is None else [points[i] for i in sample]
        return mean([cost(parts[name][p], w, b) for p in chosen])

    def ratio_ci(num, den, w, b):
        if not resamples:
            return None
        values = sorted(arm_cost(num, w, b, s) / arm_cost(den, w, b, s) for s in resamples)
        return [values[int(0.025 * (len(values) - 1))], values[int(0.975 * (len(values) - 1))]]

    result = {"schema": "ic-band/v1", "weights_gae": list(WEIGHTS), "points": points,
              "reference": reference, "rho_scalar_mul_bound_gae": list(bound_ends),
              "frobenius_as_group": frobenius_as_group, "arms": {}, "gap_to_reference": {}, "pairs": []}
    for name in arms:
        mean_parts = [mean([parts[name][p][i] for p in points]) for i in range(3)]
        result["arms"][name] = {
            "family": arms[name]["family"],
            "mean_group_ops": mean_parts[0], "mean_unpriced_native_ops": mean_parts[1],
            "mean_bounded_scalar_muls": mean_parts[2],
            "cost_gae": {"%g" % w: [arm_cost(name, w, b) for b in bound_ends] for w in WEIGHTS},
        }
    for name in arms:
        if name == reference:
            continue
        rows = {}
        for w, b in grid:
            rows.setdefault("%g" % w, []).append({
                "rho_scalar_mul_gae": b, "ratio": arm_cost(name, w, b) / arm_cost(reference, w, b),
                "ci95": ratio_ci(name, reference, w, b)})
        result["gap_to_reference"][name] = rows
    names = list(arms)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            signs, separated, cells = set(), True, []
            for w, b in grid:
                a, c = arm_cost(first, w, b), arm_cost(second, w, b)
                ci = ratio_ci(first, second, w, b)
                signs.add((a > c) - (a < c))
                if ci is None or ci[0] <= 1.0 <= ci[1]:
                    separated = False
                cells.append({"weight_gae": w, "rho_scalar_mul_gae": b, "ratio": a / c, "ci95": ci})
            if len(signs) == 1 and 0 not in signs and separated:
                cheaper = second if signs == {1} else first
                verdict = {"ranked": True, "cheaper": cheaper,
                           "statement": "%s is cheaper than %s at every weight of the band" %
                                        (cheaper, first if cheaper == second else second)}
            else:
                flips = sorted({"%g" % cell["weight_gae"] for cell in cells
                                if (cell["ratio"] > 1) != (cells[0]["ratio"] > 1)})
                verdict = {"ranked": False,
                           "statement": "unresolved: the order of %s and %s is %s" % (
                               first, second,
                               "not the same at every weight (it changes by w = %s)" % ", ".join(flips)
                               if len(signs) > 1 else
                               "the same at every weight, but the 95% interval does not exclude 1 everywhere"
                               if resamples else
                               "the same at every weight, but one point gives no interval")}
            result["pairs"].append({"arms": [first, second], "cells": cells, **verdict})
    return result


def markdown(result):
    lines = ["# Section 5a band", "",
             "Points: %d (%s). Reference: %s. Weights (GAE per unpriced native operation): %s." % (
                 len(result["points"]), ", ".join(result["points"][:6]) + (" ..." if len(result["points"]) > 6 else ""),
                 result["reference"], ", ".join("%g" % w for w in result["weights_gae"])),
             "Rho scalar multiplications not decomposed by the rho: priced at %g and %g GAE each (both ends)." %
             tuple(result["rho_scalar_mul_bound_gae"]), "",
             "| arm | mean group ops | mean unpriced native ops | cost w=0 | cost w=0.1 | cost w=1 |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name, arm in result["arms"].items():
        def cell(w):
            low, high = arm["cost_gae"][w]
            return "%.4g" % low if low == high else "%.4g-%.4g" % (low, high)
        lines.append("| %s | %.4g | %.4g | %s | %s | %s |" % (
            name, arm["mean_group_ops"], arm["mean_unpriced_native_ops"], cell("0"), cell("0.1"), cell("1")))
    lines += ["", "| gap to %s | w=0 | w=0.1 | w=1 |" % result["reference"], "| --- | ---: | ---: | ---: |"]
    for name, rows in result["gap_to_reference"].items():
        def gap(w):
            parts = []
            for row in rows[w]:
                ci = row["ci95"]
                parts.append("%.4g" % row["ratio"] + (" [%.4g, %.4g]" % tuple(ci) if ci else ""))
            return " / ".join(parts)
        lines.append("| %s | %s | %s | %s |" % (name, gap("0"), gap("0.1"), gap("1")))
    lines += ["", "Pairs (ranked only where the order holds across the band):", ""]
    lines += ["- %s vs %s: %s" % (pair["arms"][0], pair["arms"][1], pair["statement"]) for pair in result["pairs"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="band.json; band.md is written next to it")
    parser.add_argument("--draws", type=int, default=10000)
    parser.add_argument("--frobenius-as-group", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    if data.get("schema") != "ic-band-input/v1":
        raise SystemExit("input is not ic-band-input/v1")
    result = analyse(data, args.draws, frobenius_as_group=args.frobenius_as_group)
    text = markdown(result)
    if args.out:
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        args.out.with_suffix(".md").write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
