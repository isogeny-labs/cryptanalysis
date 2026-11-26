#!/usr/bin/env python3
"""Measure row-span merging for paired evaluation transversals."""

from collections import Counter
from itertools import combinations, product
import json
from pathlib import Path
from random import Random

from paired_arrangement_mobius import candidate_rows
from signed_hankel_minrank import rank_mod
from toy_jacobian import GenusTwo


PRIME = 101
SEED = 71_552_909


def canonical_row_space(matrix, prime):
    rows = [[value % prime for value in row] for row in matrix]
    if not rows:
        return ()
    row_count = len(rows)
    columns = len(rows[0])
    rank = 0
    for column in range(columns):
        pivot = next(
            (index for index in range(rank, row_count) if rows[index][column]),
            None,
        )
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column], -1, prime)
        rows[rank] = [value * inverse % prime for value in rows[rank]]
        for index in range(row_count):
            if index == rank or not rows[index][column]:
                continue
            scale = rows[index][column]
            rows[index] = [
                (left - scale * right) % prime
                for left, right in zip(rows[index], rows[rank], strict=True)
            ]
        rank += 1
        if rank == row_count:
            break
    return tuple(tuple(row) for row in rows[:rank])


def state_profile(rows, selected_slots, ambient_rank, prime):
    selected_slots = tuple(selected_slots)
    spaces = Counter()
    for choices in product((0, 1), repeat=len(selected_slots)):
        matrix = [
            rows[2 * slot + choice]
            for slot, choice in zip(selected_slots, choices, strict=True)
        ]
        space = canonical_row_space(matrix, prime)
        spaces[space] += 1
    assignment_rank_histogram = Counter()
    for space, multiplicity in spaces.items():
        assignment_rank_histogram[len(space)] += multiplicity
    nonfull = {
        space: multiplicity
        for space, multiplicity in spaces.items()
        if len(space) < ambient_rank
    }
    return {
        "assignments": 1 << len(selected_slots),
        "distinct_span_states": len(spaces),
        "maximum_state_multiplicity": max(spaces.values(), default=0),
        "assignment_rank_histogram": {
            str(rank): count
            for rank, count in sorted(assignment_rank_histogram.items())
        },
        "distinct_nonfull_span_states": len(nonfull),
        "nonfull_assignments": sum(nonfull.values()),
    }


def histogram(records, field):
    return {
        str(value): count
        for value, count in sorted(Counter(
            record[field] for record in records
        ).items())
    }


def analyze(rows, slots, ambient_rank, prime):
    natural = [
        state_profile(rows, range(size), ambient_rank, prime)
        for size in range(1, slots + 1)
    ]
    balanced_size = slots // 2
    balanced = [
        state_profile(rows, selected, ambient_rank, prime)
        for selected in combinations(range(slots), balanced_size)
    ]
    prefull_size = ambient_rank - 1
    prefull = [
        state_profile(rows, selected, ambient_rank, prime)
        for selected in combinations(range(slots), prefull_size)
    ]
    saturation_size = ambient_rank
    saturation = [
        state_profile(rows, selected, ambient_rank, prime)
        for selected in combinations(range(slots), saturation_size)
    ]
    return {
        "natural_prefix_profiles": natural,
        "balanced_slot_size": balanced_size,
        "balanced_distinct_state_histogram": histogram(
            balanced, "distinct_span_states"
        ),
        "balanced_maximum_state_multiplicity_histogram": histogram(
            balanced, "maximum_state_multiplicity"
        ),
        "prefull_slot_size": prefull_size,
        "prefull_distinct_state_histogram": histogram(
            prefull, "distinct_span_states"
        ),
        "prefull_maximum_state_multiplicity_histogram": histogram(
            prefull, "maximum_state_multiplicity"
        ),
        "saturation_slot_size": saturation_size,
        "saturation_nonfull_assignment_histogram": histogram(
            saturation, "nonfull_assignments"
        ),
        "saturation_nonfull_state_histogram": histogram(
            saturation, "distinct_nonfull_span_states"
        ),
    }


def extended_panel(curve, dimension, rng):
    slots = dimension + 2
    split = [
        (x, curve.roots(x))
        for x in range(curve.p)
        if len(curve.roots(x)) == 2
    ]
    for attempt in range(1_000):
        chosen = rng.sample(split, slots)
        selected = [(x, roots[rng.randrange(2)]) for x, roots in chosen]
        total = curve.identity
        for x, y in selected:
            total = curve.add(total, curve.point_divisor(x, y))
        u, v = curve.neg(total)
        if len(u) != 3:
            continue
        if any(curve.poly.evaluate(u, x) == 0 for x, _ in selected):
            continue
        panel = {
            "projective_section_dimension": dimension,
            "split_abscissae": [x for x, _ in selected],
            "target_u": u,
            "target_v": v,
        }
        rows = candidate_rows(curve, panel)
        selected_rows = []
        for slot, (_, y) in enumerate(selected):
            roots = chosen[slot][1]
            selected_rows.append(rows[2 * slot + roots.index(y)])
        if rank_mod(selected_rows, curve.p) != dimension:
            continue
        return rows, attempt + 1
    raise AssertionError("failed to build extended panel")


def main():
    source = json.loads(
        Path(__file__).with_name("binary_split_norm_control.json").read_text()
    )
    curve = GenusTwo(PRIME)
    panels = []
    for panel in source["panels"]:
        rows = candidate_rows(curve, panel)
        ambient_rank = panel["projective_section_dimension"] + 1
        record = {
            "tail_slots": panel["tail_slots"],
            "ambient_rank": ambient_rank,
            "panel_source": "binary_split_norm_control.json",
        }
        record.update(analyze(
            rows, panel["tail_slots"], ambient_rank, curve.p
        ))
        panels.append(record)
    rng = Random(SEED)
    for dimension in range(8, 11):
        rows, attempts = extended_panel(curve, dimension, rng)
        slots = dimension + 2
        record = {
            "tail_slots": slots,
            "ambient_rank": dimension + 1,
            "panel_source": "extended planted divisor",
            "construction_attempts": attempts,
        }
        record.update(analyze(rows, slots, dimension + 1, curve.p))
        panels.append(record)
    result = {
        "prime": PRIME,
        "genus": 2,
        "seed": SEED,
        "sources": [
            "binary_split_norm_control.json",
            "extended planted divisors from toy_jacobian.py",
        ],
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
