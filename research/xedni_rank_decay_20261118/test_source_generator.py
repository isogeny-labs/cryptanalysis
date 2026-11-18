#!/usr/bin/env python3
"""Controls for deterministic Xedni prime and finite-field source generation."""

from __future__ import annotations

import json
import math
from pathlib import Path
import unittest

import field
import prime_manifest
import source_generator


def brute_cardinality(prime: int, a: int, b: int):
    total = 1
    for x in range(prime):
        rhs = (x**3 + a * x + b) % prime
        symbol = field.legendre(rhs, prime)
        total += 1 if symbol == 0 else 2 if symbol == 1 else 0
    factors = []
    remainder = total
    candidate = 2
    while candidate * candidate <= remainder:
        exponent = 0
        while remainder % candidate == 0:
            remainder //= candidate
            exponent += 1
        if exponent:
            factors.append((candidate, exponent))
        candidate += 1
    if remainder > 1:
        factors.append((remainder, 1))
    return total, factors


class SmallBackend:
    name = "small-control-backend"

    def cardinality_and_factors(self, prime, a, b):
        if prime > 257:
            raise AssertionError("test backend refuses non-small point counts")
        return brute_cardinality(prime, a, b)


class PrimeManifestTests(unittest.TestCase):
    def test_all_bit_sizes_and_slots(self):
        value = prime_manifest.manifest()
        prime_manifest.validate(value)
        rows = value["primes"]
        self.assertEqual(len(rows), 27)
        for bits in prime_manifest.BIT_SIZES:
            selected = [row["prime"] for row in rows if row["bits"] == bits]
            self.assertEqual(len(selected), 3)
            self.assertEqual(len(set(selected)), 3)
            self.assertTrue(all(p.bit_length() == bits for p in selected))

    def test_retained_manifest_matches_generator_and_hash(self):
        retained = json.loads(Path(__file__).with_name("PRIMES.json").read_text())
        prime_manifest.validate(retained)

    def test_miller_rabin_edges_and_pseudoprimes(self):
        for prime in (2, 3, 5, 65521, 4294967291):
            self.assertTrue(prime_manifest.is_prime_u32(prime))
        for composite in (0, 1, 4, 9, 341, 561, 1105, 3215031751, 4294967295):
            self.assertFalse(prime_manifest.is_prime_u32(composite))
        with self.assertRaises(ValueError):
            prime_manifest.is_prime_u32(2**32)


class FieldTests(unittest.TestCase):
    def test_tonelli_shanks_at_every_manifest_size(self):
        for row in prime_manifest.derive_primes():
            prime = row["prime"]
            seed = row["bits"] * 100 + row["slot"] + 7
            square = seed * seed % prime
            root = field.tonelli_shanks(square, prime)
            self.assertIsNotNone(root)
            self.assertEqual(root * root % prime, square)
            nonresidue = 2
            while field.legendre(nonresidue, prime) != -1:
                nonresidue += 1
            self.assertIsNone(field.tonelli_shanks(nonresidue, prime))

    def test_fresh_curve_and_point_sampling_without_counts(self):
        for row in prime_manifest.derive_primes():
            prime = row["prime"]
            for family in ("generic", "j0"):
                curves = []
                for index in range(2):
                    stream = field.HashStream(
                        f"curve-control|{prime}|{family}|{index}"
                    )
                    a, b, _ = field.generate_curve(stream, prime, family)
                    self.assertNotEqual(field.discriminant(a, b, prime), 0)
                    if family == "j0":
                        self.assertEqual(a, 0)
                    point, _ = field.sample_point(stream, prime, a, b)
                    self.assertTrue(field.on_curve(point, a, b, prime))
                    curves.append((a, b))
                self.assertEqual(len(set(curves)), len(curves))

    def test_group_law_small_curve(self):
        prime, a, b = 101, 2, 3
        stream = field.HashStream("group-law-control")
        point, _ = field.sample_point(stream, prime, a, b)
        self.assertIsNone(
            field.point_add(point, field.point_neg(point, prime), a, prime)
        )
        self.assertEqual(
            field.point_mul(5, point, a, prime),
            field.point_add(
                field.point_mul(2, point, a, prime),
                field.point_mul(3, point, a, prime),
                a,
                prime,
            ),
        )


class SourceTests(unittest.TestCase):
    def test_small_source_is_deterministic_and_prefixes_are_nested(self):
        arguments = (101, "generic", 4, 9, "source-control", SmallBackend())
        first = source_generator.generate_source(*arguments)
        second = source_generator.generate_source(*arguments)
        self.assertEqual(first, second)
        self.assertEqual(json.loads(source_generator.render_json(first)), first)
        self.assertEqual(
            json.loads(source_generator.render_jsonl([first]).strip()), first
        )
        permutation = first["prefix_permutation"]
        self.assertEqual(sorted(permutation), list(range(9)))
        for r in range(2, 10):
            prefix = first["prefixes"][str(r)]
            self.assertEqual(prefix["indices"], permutation[:r])
            self.assertEqual(prefix["target_index"], permutation[r - 1])
        points = [tuple(point) for point in first["ordered_points"]]
        negatives = [field.point_neg(point, first["p"]) for point in points]
        self.assertEqual(len(set(points) | set(negatives)), 18)
        subgroup_order = first["source_subgroup_order"]
        cofactor = first["source_cofactor"]
        self.assertTrue(prime_manifest.is_prime_u32(subgroup_order))
        self.assertEqual(subgroup_order * cofactor, first["cardinality"])
        self.assertIsNotNone(tuple(first["base_point"]))
        self.assertIsNone(
            field.point_mul(
                subgroup_order,
                tuple(first["base_point"]),
                first["curve"]["a"],
                first["p"],
            )
        )

    def test_factorization_validation_and_fail_closed_backend(self):
        source_generator.validate_factorization(2**3 * 5, [(2, 3), (5, 1)])
        for cardinality, factors in ((40, [(2, 2), (5, 1)]), (40, [(4, 1), (10, 1)])):
            with self.assertRaises(ValueError):
                source_generator.validate_factorization(cardinality, factors)
        with self.assertRaises(source_generator.BackendUnavailable):
            source_generator.PariBackend("definitely-no-such-gp-executable")
        with self.assertRaises(source_generator.BackendUnavailable):
            source_generator.PariContainerBackend(
                "xedni-pari@sha256:control", "definitely-no-such-runtime"
            )
        container = source_generator.PariContainerBackend(
            "xedni-pari@sha256:control", "true"
        )
        self.assertIn("--network=none", container.command)
        self.assertEqual(
            container.command[container.command.index("--entrypoint") + 1], "gp"
        )
        self.assertEqual(container.command[-3:], ["xedni-pari@sha256:control", "-q", "-f"])

    def test_hasse_formula_uses_constant_time_integer_bound(self):
        for row in prime_manifest.derive_primes():
            prime = row["prime"]
            radius = source_generator.hasse_radius(prime)
            self.assertEqual(radius, math.isqrt(4 * prime))
            self.assertLess(radius, 2**17)


if __name__ == "__main__":
    unittest.main()
