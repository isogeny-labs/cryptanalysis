#!/usr/bin/env python3
"""Frobenius orbit certificate for the P-256 Aronhold characteristics."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


# Columns of Tian's relation (L_i-delta)=(D_1,...,D_6)M.
ARONHOLD_MATRIX_ROWS = (
    (1, 0, 0, 1, 1, 1, 0),
    (1, 0, 1, 0, 0, 1, 1),
    (1, 1, 1, 1, 0, 0, 0),
    (1, 0, 0, 1, 1, 0, 1),
    (1, 1, 0, 0, 0, 1, 1),
    (1, 1, 1, 0, 1, 0, 0),
)


def xor(left, right):
    return tuple(x ^ y for x, y in zip(left, right))


def parity(characteristic):
    return sum(characteristic[i] * characteristic[i + 3] for i in range(3)) % 2


def linear_frobenius(characteristic):
    """q1->q2, q2->q1+q2 on each P-256 E[2] factor."""
    top, bottom = characteristic[:3], characteristic[3:]
    return tuple(bottom) + tuple(top[i] ^ bottom[i] for i in range(3))


def build_certificate():
    characteristics = list(itertools.product(range(2), repeat=6))
    columns = [
        tuple(ARONHOLD_MATRIX_ROWS[row][column] for row in range(6))
        for column in range(7)
    ]
    deltas = [
        value
        for value in characteristics
        if parity(value) == 0
        and all(parity(xor(value, column)) == 1 for column in columns)
    ]
    if deltas != [(0, 0, 0, 0, 0, 0)]:
        raise AssertionError("Aronhold even characteristic is not unique")
    aronhold = [xor(deltas[0], column) for column in columns]

    corrections = [
        correction
        for correction in characteristics
        if all(
            parity(xor(linear_frobenius(value), correction)) == parity(value)
            for value in characteristics
        )
    ]
    if corrections != [(0, 0, 0, 1, 1, 1)]:
        raise AssertionError("theta-characteristic affine correction is not unique")
    correction = corrections[0]

    def frobenius(value):
        return xor(linear_frobenius(value), correction)

    odd = {value for value in characteristics if parity(value)}
    pairwise = {
        xor(aronhold[left], aronhold[right])
        for left in range(7)
        for right in range(left + 1, 7)
    }
    if set(aronhold) | pairwise != odd or len(pairwise) != 21:
        raise AssertionError("Aronhold system did not label all 28 odd characteristics")

    unvisited = set(odd)
    orbits = []
    while unvisited:
        start = min(unvisited)
        orbit = []
        value = start
        while value not in orbit:
            orbit.append(value)
            value = frobenius(value)
        if value != start:
            raise AssertionError("Frobenius orbit did not close at its start")
        unvisited.difference_update(orbit)
        orbits.append(orbit)
    histogram = {}
    for orbit in orbits:
        histogram[len(orbit)] = histogram.get(len(orbit), 0) + 1

    images = [frobenius(value) for value in aronhold]
    membership = [image in aronhold for image in images]
    return {
        "format": "p256-aronhold-frobenius-certificate-v1",
        "frobenius_on_each_symplectic_pair": "(top,bottom) -> (bottom,top+bottom)",
        "affine_theta_characteristic_correction": list(correction),
        "unique_even_delta": list(deltas[0]),
        "aronhold_characteristics": [list(value) for value in aronhold],
        "frobenius_images": [list(value) for value in images],
        "images_remaining_in_selected_aronhold_system": sum(membership),
        "selected_aronhold_stable": all(membership),
        "all_odd_characteristics_count": len(odd),
        "remaining_odd_as_pairwise_aronhold_sums": len(pairwise),
        "full_odd_frobenius_orbit_histogram": {
            str(length): count for length, count in sorted(histogram.items())
        },
        "rational_bitangent_count_predicted": histogram.get(1, 0),
        "descent_consequence": (
            "only one of the seven known Aronhold lines is Frobenius-stable; "
            "the other six map among the 21 unconstructed bitangents, so the "
            "seven-line data alone cannot determine the projective Frobenius isomorphism"
        ),
        "next_exact_gate": "construct the remaining 21 bitangent equations or run the preserved ternary-quartic isomorphism diagnostic",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(build_certificate(), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
