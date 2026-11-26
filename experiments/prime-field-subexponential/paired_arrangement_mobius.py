#!/usr/bin/env python3
"""Measure the arrangement state count of paired section evaluations."""

from collections import Counter
import json
from math import comb
from pathlib import Path

from multisection_span_control import section_basis
from signed_hankel_minrank import rank_mod
from toy_jacobian import GenusTwo


PRIME = 101


def candidate_rows(curve, panel):
    basis = section_basis(
        curve.poly,
        panel["target_u"],
        panel["target_v"],
        panel["projective_section_dimension"],
    )
    rows = []
    for x in panel["split_abscissae"]:
        roots = curve.roots(x)
        assert len(roots) == 2
        for y in roots:
            rows.append([
                (
                    curve.poly.evaluate(basis_b, x) * y
                    - curve.poly.evaluate(basis_a, x)
                ) % curve.p
                for basis_b, basis_a in basis
            ])
    return rows


def subset_rank(rows, mask, prime):
    return rank_mod(
        [row for index, row in enumerate(rows) if mask >> index & 1],
        prime,
    ) if mask else 0


def analyze(rows, prime):
    elements = len(rows)
    rank = rank_mod(rows, prime)
    characteristic = Counter()
    rank_histogram = Counter()
    dependent_by_size = Counter()
    bases = 0
    for mask in range(1 << elements):
        size = mask.bit_count()
        subset = subset_rank(rows, mask, prime)
        rank_histogram[subset] += 1
        characteristic[rank - subset] += -1 if size % 2 else 1
        if subset < min(size, rank):
            dependent_by_size[size] += 1
        if size == rank and subset == rank:
            bases += 1

    mobius = abs(characteristic[0])
    uniform_mobius = comb(elements - 1, rank - 1)
    uniform_bases = comb(elements, rank)
    return {
        "elements": elements,
        "rank": rank,
        "bases": bases,
        "uniform_bases": uniform_bases,
        "base_defect": uniform_bases - bases,
        "top_orlik_solomon_dimension": mobius,
        "uniform_top_dimension": uniform_mobius,
        "top_dimension_defect": uniform_mobius - mobius,
        "characteristic_polynomial_coefficients": {
            str(exponent): coefficient
            for exponent, coefficient in sorted(characteristic.items())
            if coefficient
        },
        "dependent_subsets_by_size": {
            str(size): count
            for size, count in sorted(dependent_by_size.items())
        },
        "rank_histogram": {
            str(value): count for value, count in sorted(rank_histogram.items())
        },
    }


def main():
    source = json.loads(
        Path(__file__).with_name("binary_split_norm_control.json").read_text()
    )
    curve = GenusTwo(PRIME)
    panels = []
    for panel in source["panels"]:
        rows = candidate_rows(curve, panel)
        record = {
            "projective_section_dimension": panel[
                "projective_section_dimension"
            ],
            "tail_slots": panel["tail_slots"],
        }
        record.update(analyze(rows, curve.p))
        panels.append(record)
    result = {
        "prime": PRIME,
        "genus": 2,
        "source": "binary_split_norm_control.json",
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
