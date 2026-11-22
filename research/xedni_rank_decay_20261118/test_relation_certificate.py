#!/usr/bin/env python3
"""Synthetic-only controls for exact supplied-relation certificates."""

from __future__ import annotations

import copy
from fractions import Fraction
import json
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze
import lift_builder
import relation_certificate as relation
import source_generator


def synthetic_source(r: int) -> tuple[dict, list[int]]:
    """Return a tiny planted fixture; none is a natural experiment row."""
    if r == 2:
        scalars = [1, 3]
        points = [[1, 1], [6, 5]]
        coefficients = [-2, -3]
        p, a, b, q, base = 7, 1, 6, 11, [1, 1]
    elif 3 <= r <= 6:
        scalar_rows = {
            3: [2, 5, 6],
            4: [2, 5, 1, 6],
            5: [2, 5, 1, 3, 6],
            6: [2, 5, 1, 3, 4, 6],
        }
        point_by_scalar = {
            1: [1, 2],
            2: [6, 3],
            3: [2, 2],
            4: [4, 5],
            5: [3, 3],
            6: [5, 3],
        }
        scalars = scalar_rows[r]
        points = [point_by_scalar[scalar] for scalar in scalars]
        coefficients = [1, 1] + [0] * (r - 3) + [1]
        p, a, b, q, base = 7, 0, 3, 13, [1, 2]
    else:
        raise ValueError("synthetic source only covers r=2..6")
    source = {
        "schema": source_generator.SCHEMA,
        "master_seed": f"synthetic-relation-r{r}",
        "source_id": f"synthetic-relation-r{r}",
        "source_index": 0,
        "p": p,
        "bits": p.bit_length(),
        "family": "generic",
        "curve": {"a": a, "b": b, "generation_attempts": 1},
        "cardinality": q,
        "cardinality_factors": [[q, 1]],
        "cardinality_backend": "hand-certified-synthetic-control",
        "source_subgroup_order": q,
        "source_cofactor": 1,
        "base_point": base,
        "base_point_order": q,
        "point_sampling_attempts": 1,
        "scalar_sampling_attempts": r,
        "max_r": r,
        "ordered_scalars": scalars,
        "ordered_points": points,
        "prefix_permutation": list(range(r)),
        "prefixes": {
            str(r): {"indices": list(range(r)), "target_index": r - 1}
        },
    }
    return source, coefficients


class RelationCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = {}
        for r in range(2, 7):
            source, coefficients = synthetic_source(r)
            lift = lift_builder.build_lift(source, r, "balanced")
            cls.fixtures[r] = source, lift, coefficients

    def test_exact_replay_source_reduction_and_recovery_r2_through_r6(self):
        for r, (source, lift, coefficients) in self.fixtures.items():
            with self.subTest(r=r):
                certificate = relation.build_relation_certificate(
                    lift, source, coefficients
                )
                certificate = json.loads(json.dumps(certificate))
                self.assertEqual(
                    relation.verify_relation_certificate(certificate, lift, source),
                    [],
                )
                self.assertEqual(
                    analyze._validate_outcome(certificate["outcome"], "certificate.outcome"),
                    certificate["outcome"],
                )
                self.assertEqual(certificate["r"], r)
                self.assertTrue(certificate["relation"]["nonzero"])
                self.assertTrue(certificate["relation"]["supplied_primitive"])
                self.assertTrue(certificate["relation"]["certified_primitive"])
                self.assertTrue(certificate["relation"]["primitive_replays_exactly"])
                self.assertTrue(
                    certificate["rational_replay"]["supplied_sum_is_identity"]
                )
                self.assertTrue(
                    certificate["rational_replay"]["certified_sum_is_identity"]
                )
                self.assertEqual(
                    certificate["source_reduction"]["scalar_relation_residue"], 0
                )
                self.assertTrue(
                    certificate["source_reduction"]["finite_field_group_sum_is_identity"]
                )
                self.assertTrue(
                    certificate["recovery"]["target_coefficient_invertible"]
                )
                self.assertEqual(
                    certificate["recovery"]["induced_target_equation_residue"], 0
                )
                self.assertTrue(certificate["recovery"]["recovered_scalar_replay"])
                self.assertEqual(
                    certificate["recovery"]["recovered_scalar"],
                    source["ordered_scalars"][-1],
                )
                if r == 2:
                    self.assertEqual(
                        certificate["classification"]["relation_class"], "nontrivial"
                    )
                    self.assertTrue(
                        certificate["classification"][
                            "qualifies_as_primitive_nontrivial"
                        ]
                    )
                    self.assertEqual(
                        certificate["outcome"]["useful_recovery"], "CERT_YES"
                    )
                else:
                    self.assertEqual(
                        certificate["classification"]["relation_class"], "line"
                    )
                    self.assertFalse(certificate["classification"]["nontrivial"])
                    self.assertEqual(
                        certificate["outcome"]["useful_recovery"], "CERT_YES"
                    )

    def test_generalized_group_law_uses_exact_fractions(self):
        source, lift, coefficients = self.fixtures[2]
        ainvs = tuple(Fraction(value) for value in lift["ainvs"])
        points = [tuple(Fraction(value) for value in point) for point in lift["points"]]
        self.assertTrue(all(relation.on_curve(point, ainvs) for point in points))
        self.assertEqual(
            relation.point_add(points[0], relation.point_neg(points[0], ainvs), ainvs),
            None,
        )
        self.assertIsNone(relation.relation_sum(coefficients, points, ainvs))
        doubled = relation.point_mul(2, points[0], ainvs)
        self.assertTrue(relation.on_curve(doubled, ainvs))
        self.assertTrue(all(isinstance(coordinate, Fraction) for coordinate in doubled))

    def test_nonprimitive_relation_is_canonicalized_before_outcome(self):
        source, lift, coefficients = self.fixtures[2]
        doubled = [2 * coefficient for coefficient in coefficients]
        certificate = relation.build_relation_certificate(lift, source, doubled)
        self.assertFalse(certificate["relation"]["supplied_primitive"])
        self.assertTrue(certificate["relation"]["certified_primitive"])
        self.assertEqual(certificate["relation"]["coefficient_gcd"], 2)
        self.assertTrue(certificate["relation"]["primitive_replays_exactly"])
        self.assertEqual(certificate["relation"]["certified_coefficients"], [2, 3])
        self.assertEqual(
            certificate["classification"]["relation_class"], "nontrivial"
        )
        self.assertTrue(
            certificate["classification"]["qualifies_as_primitive_nontrivial"]
        )
        self.assertTrue(certificate["recovery"]["recovered_scalar_replay"])
        self.assertTrue(
            certificate["classification"]["eligible_for_nontrivial_endpoint"]
        )
        self.assertEqual(certificate["outcome"]["useful_recovery"], "CERT_YES")

    def test_noninvertible_target_is_exact_dependence_but_not_recovery(self):
        source, _ = synthetic_source(4)
        source = copy.deepcopy(source)
        source["source_id"] = "synthetic-noninvertible-r4"
        source["ordered_scalars"] = [2, 5, 6, 1]
        source["ordered_points"] = [[6, 3], [3, 3], [5, 3], [1, 2]]
        lift = lift_builder.build_lift(source, 4, "balanced")
        certificate = relation.build_relation_certificate(
            lift, source, [1, 1, 1, 0]
        )
        self.assertTrue(certificate["relation"]["supplied_primitive"])
        self.assertFalse(certificate["recovery"]["target_coefficient_invertible"])
        self.assertIsNone(certificate["recovery"]["recovered_scalar"])
        self.assertFalse(certificate["recovery"]["recovered_scalar_replay"])
        self.assertEqual(
            certificate["outcome"]["target_coefficient_invertible"], "CERT_NO"
        )
        self.assertEqual(certificate["outcome"]["useful_recovery"], "CERT_NO")

    def test_zero_and_false_relations_fail_closed(self):
        source, lift, coefficients = self.fixtures[4]
        with self.assertRaisesRegex(relation.RelationCertificateError, "zero vector"):
            relation.build_relation_certificate(lift, source, [0] * 4)
        changed = list(coefficients)
        changed[0] += 1
        with self.assertRaisesRegex(relation.RelationCertificateError, "does not sum"):
            relation.build_relation_certificate(lift, source, changed)
        with self.assertRaises(relation.RelationCertificateError):
            relation.build_relation_certificate(lift, source, [True, 1, 0, 1])

    def test_strict_hash_and_full_certificate_validation(self):
        source, lift, coefficients = self.fixtures[2]
        certificate = relation.build_relation_certificate(lift, source, coefficients)
        mutations = []
        changed = copy.deepcopy(certificate)
        changed["recovery"]["recovered_scalar"] += 1
        mutations.append(changed)
        changed = copy.deepcopy(certificate)
        changed["recovery"]["recovered_scalar"] += 1
        without_digest = dict(changed)
        without_digest.pop("certificate_sha256")
        changed["certificate_sha256"] = relation.object_sha256(without_digest)
        mutations.append(changed)
        changed = copy.deepcopy(certificate)
        changed["unrecognized"] = True
        without_digest = dict(changed)
        without_digest.pop("certificate_sha256")
        changed["certificate_sha256"] = relation.object_sha256(without_digest)
        mutations.append(changed)
        for mutation in mutations:
            self.assertNotEqual(
                relation.verify_relation_certificate(mutation, lift, source), []
            )

        changed_lift = copy.deepcopy(lift)
        changed_lift["points"][0][0] += 1
        self.assertNotEqual(
            relation.verify_relation_certificate(
                certificate, changed_lift, source
            ),
            [],
        )
        changed_lift = copy.deepcopy(lift)
        changed_lift["certificate"]["unrecognized_true_flag"] = True
        self.assertNotEqual(
            relation.verify_relation_certificate(
                certificate, changed_lift, source
            ),
            [],
        )
        changed_source = copy.deepcopy(source)
        changed_source["ordered_scalars"][0] += 1
        self.assertNotEqual(
            relation.verify_relation_certificate(
                certificate, lift, changed_source
            ),
            [],
        )

    def test_external_proposals_count_only_after_exact_replay(self):
        source, lift, coefficients = self.fixtures[3]
        false_candidate = list(coefficients)
        false_candidate[0] += 1
        replay = relation.replay_supplied_candidates(
            lift, source, [false_candidate, coefficients]
        )
        self.assertEqual(replay["proposal_count"], 2)
        self.assertEqual(replay["exact_replay_count"], 1)
        self.assertEqual(replay["counted_relation_count"], 1)
        self.assertFalse(replay["absence_certificate"])
        self.assertEqual(
            replay["selected_dependence_if_no_exact_replay"], "UNKNOWN"
        )
        self.assertFalse(replay["proposals"][0]["accepted"])
        self.assertTrue(replay["proposals"][1]["accepted"])

    def test_heuristic_finder_is_explicitly_unavailable(self):
        status = relation.finder_status()
        self.assertFalse(status["implemented"])
        self.assertEqual(status["external_backend"], "relation_pari.py")
        self.assertIn("exact certificate replay", status["acceptance_rule"])
        with self.assertRaisesRegex(
            relation.RelationCertificateError, "intentionally separated"
        ):
            relation.propose_relations()


if __name__ == "__main__":
    unittest.main()
