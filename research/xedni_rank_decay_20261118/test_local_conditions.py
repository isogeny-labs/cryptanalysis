#!/usr/bin/env python3
"""Unit controls for local_conditions.py; no natural rank rows are generated."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_conditions as local


class LocalConditionTests(unittest.TestCase):
    def test_prime_pool(self):
        self.assertEqual(local.primes_7_to_97()[0], 7)
        self.assertEqual(local.primes_7_to_97()[-1], 97)
        self.assertEqual(len(local.primes_7_to_97()), 22)

    def test_target_counts(self):
        self.assertEqual(local.target_point_count("B_reverse_mestre", 7), 3)
        self.assertEqual(local.target_point_count("B_reverse_mestre_plus1", 7), 4)
        self.assertEqual(local.target_point_count("B_reverse_mestre_plus2", 7), 5)
        self.assertEqual(local.target_point_count("P_neutral_crt", 7), 8)
        self.assertEqual(local.target_point_count("I_incompatible", 7), 3)

    def test_A_none(self):
        result = local.build_local_conditions("A_none", 6)
        self.assertEqual(result["M"], 1)
        self.assertEqual(result["compatibility"]["status"], "vacuous")
        self.assertEqual(local.check_local_conditions(result), [])

    def test_reverse_mestre_and_common_quotient(self):
        result = local.build_local_conditions(
            "B_reverse_mestre", 2, [7, 11], seed="reverse-control"
        )
        self.assertEqual([entry["point_count"] for entry in result["local"]], [3, 6])
        self.assertEqual(result["M"], 77)
        self.assertEqual(result["compatibility"]["status"], "certified")
        pair = result["compatibility"]["pairs"][0]
        self.assertEqual(pair["common_order_gcd"], 3)
        self.assertEqual(pair["quotient_divisors"], [3])
        self.assertEqual(local.check_local_conditions(result), [])

    def test_reverse_mestre_secondary_offsets(self):
        for offset, arm in enumerate(
            ("B_reverse_mestre", "B_reverse_mestre_plus1", "B_reverse_mestre_plus2")
        ):
            result = local.build_local_conditions(arm, 2, [7], seed=f"offset-{offset}")
            self.assertEqual(result["local"][0]["point_count"], 3 + offset)
            self.assertEqual(local.check_local_conditions(result), [])

    def test_neutral_crt(self):
        result = local.build_local_conditions("P_neutral_crt", 3, [7, 11], seed="neutral")
        self.assertEqual([entry["point_count"] for entry in result["local"]], [12])
        self.assertEqual(
            result["prime_rejections"][0],
            {
                "prime": 7,
                "reason": "fewer_than_r_usable_affine_points",
                "selection_arm": "B_reverse_mestre",
                "selection_point_count": 3,
                "usable_affine_points": 2,
            },
        )
        self.assertEqual(local.check_local_conditions(result), [])

    def test_ineligible_prime_is_retained_as_rejection(self):
        result = local.build_local_conditions("B_reverse_mestre", 4, [7, 11], seed="skip")
        self.assertEqual(result["accepted_primes"], [11])
        self.assertEqual(
            result["prime_rejections"][0]["reason"],
            "fewer_than_r_usable_affine_points",
        )
        self.assertEqual(local.check_local_conditions(result), [])

    def test_order_seven_is_not_usable_for_six_weierstrass_rows(self):
        eligibility = local.eligible_primes("B_reverse_mestre", 6, [13, 17])
        self.assertEqual(eligibility["accepted"], [17])
        self.assertEqual(
            eligibility["rejected"][0]["reason"],
            "weierstrass_incidence_rank_at_most_5",
        )

        # Exhaust the two pool cases where a frozen target order is seven:
        # B at 13 and B+1 at 11.  The six affine rows never reach rank six.
        for prime in (11, 13):
            order_seven_curves = 0
            for a in range(prime):
                for b in range(prime):
                    curve = local.Curve(prime, a, b)
                    if not local.is_nonsingular(curve):
                        continue
                    points = local.curve_points(curve)
                    if len(points) != 7:
                        continue
                    order_seven_curves += 1
                    affine = [point for point in points if point is not None]
                    rank = local.matrix_rank_mod(
                        [
                            local.weierstrass_incidence_row(point, prime)
                            for point in affine
                        ],
                        prime,
                    )
                    self.assertLessEqual(rank, 5)
            self.assertGreater(order_seven_curves, 0)

    def test_product_prefix(self):
        prefix = local.prime_prefix_for_product("B_reverse_mestre", 4, 100)
        self.assertGreaterEqual(prefix["product"], 100)
        result = local.build_local_conditions(
            "B_reverse_mestre", 4, target_product=100, seed="product"
        )
        self.assertGreaterEqual(result["M"], 100)
        self.assertEqual(local.check_local_conditions(result), [])

    def test_p_and_i_use_bs_frozen_prime_schedule(self):
        for r in range(2, 7):
            b = local.prime_prefix_for_product("B_reverse_mestre", r, 2**32)
            p = local.prime_prefix_for_product("P_neutral_crt", r, 2**32)
            incompatible = local.prime_prefix_for_product("I_incompatible", r, 2**32)
            self.assertEqual(p["primes"], b["primes"])
            self.assertEqual(incompatible["primes"], b["primes"])
            self.assertEqual(p["product"], b["product"])
            self.assertEqual(incompatible["product"], b["product"])

    def test_seeded_output_is_deterministic_and_json_checkable(self):
        arguments = ("B_reverse_mestre_plus2", 5, [11, 13, 17])
        first = local.build_local_conditions(*arguments, seed="determinism")
        second = local.build_local_conditions(*arguments, seed="determinism")
        self.assertEqual(first, second)
        self.assertEqual(local.check_local_conditions(json.loads(json.dumps(first))), [])

    def test_tamper_M_rejected(self):
        result = local.build_local_conditions("B_reverse_mestre", 2, [7, 11], seed="tamper-M")
        changed = copy.deepcopy(result)
        changed["M"] += 1
        self.assertIn("M", local.check_local_conditions(changed))

    def test_tamper_point_rejected(self):
        result = local.build_local_conditions("P_neutral_crt", 2, [7], seed="tamper-point")
        changed = copy.deepcopy(result)
        changed["local"][0]["selected_points"][1] = changed["local"][0]["selected_points"][0]
        self.assertTrue(
            any(
                error.startswith("distinct_points")
                for error in local.check_local_conditions(changed)
            )
        )

    def test_tamper_compatibility_rejected(self):
        result = local.build_local_conditions(
            "B_reverse_mestre", 2, [7, 11], seed="tamper-compatibility"
        )
        changed = copy.deepcopy(result)
        changed["compatibility"]["pairs"][0]["shared_scalar_residues"]["3"][0] ^= 1
        self.assertIn("compatibility_pairs", local.check_local_conditions(changed))

    def test_deliberately_incompatible_known_negative(self):
        result = local.build_local_conditions(
            "I_incompatible", 2, [7, 11], seed="known-negative"
        )
        self.assertEqual(result["M"], 77)
        self.assertFalse(result["primary_estimand_eligible"])
        self.assertEqual(
            result["compatibility"]["status"], "deliberately_incompatible"
        )
        certificate = result["compatibility"]["incompatibility"]
        self.assertTrue(certificate["mismatch"])
        self.assertNotEqual(
            certificate["left_quotient_image"],
            certificate["right_quotient_image"],
        )
        self.assertEqual(certificate["quotient_isomorphism_units"], [])
        self.assertFalse(certificate["quotient_tuples_isomorphic"])
        self.assertTrue(
            any(not pair["certified"] for pair in result["compatibility"]["pairs"])
        )
        self.assertEqual(local.check_local_conditions(result), [])

    def test_fake_incompatible_label_without_mutation_is_rejected(self):
        compatible = local.build_local_conditions(
            "B_reverse_mestre", 2, [7, 11], seed="fake-negative"
        )
        changed = copy.deepcopy(compatible)
        changed["arm"] = "I_incompatible"
        changed["primary_estimand_eligible"] = False
        changed["compatibility"]["status"] = "deliberately_incompatible"
        changed["compatibility"]["primary_estimand_eligible"] = False
        self.assertNotEqual(local.check_local_conditions(changed), [])

    def test_incompatible_requires_a_common_quotient(self):
        # Reverse-Mestre orders at 11 and 13 are 6 and 7.
        with self.assertRaisesRegex(local.LocalConditionError, "pairwise coprime"):
            local.build_local_conditions(
                "I_incompatible", 2, [11, 13], seed="no-common-quotient"
            )

    def test_curve_cap_fails_closed(self):
        with self.assertRaises(local.LocalConditionError):
            local.build_local_conditions(
                "B_reverse_mestre", 2, [7], seed="cap", max_curve_attempts=0
            )

    def test_malformed_certificate_fails_closed_without_exception(self):
        result = local.build_local_conditions(
            "B_reverse_mestre", 2, [7, 11], seed="malformed"
        )
        changed = copy.deepcopy(result)
        changed["local"][0]["a"] = "not-a-field-element"
        self.assertNotEqual(local.check_local_conditions(changed), [])
        self.assertEqual(local.check_local_conditions(None), ["config"])

    def test_r7_general_cubic_surrogate_fails_closed(self):
        with self.assertRaisesRegex(local.LocalConditionError, "point-map bridge"):
            local.build_local_conditions("A_none", 7)


if __name__ == "__main__":
    unittest.main()
