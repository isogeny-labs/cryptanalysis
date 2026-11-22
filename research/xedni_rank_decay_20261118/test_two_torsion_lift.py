#!/usr/bin/env python3

import math
import unittest

import two_torsion_lift as ttl


class TwoTorsionLiftTests(unittest.TestCase):
    def test_published_polynomials_and_both_parameters(self):
        expected = {
            -1793: (
                -1793727297677166359919097,
                8697425991446308729,
                8697419661053158397,
            ),
            181: (
                -1792472369211529197803773,
                8698024591934109793,
                8698018259581495997,
            ),
        }
        for parameter_n, values in expected.items():
            with self.subTest(parameter_n=parameter_n):
                result = ttl.published_example(parameter_n)
                lift = result["lift"]
                self.assertEqual(
                    (lift["b"], lift["factor_plus"], lift["factor_minus"]),
                    values,
                )
                self.assertEqual(lift["factor_gcd"], 1)
                self.assertFalse(result["boundary"]["factors_equal"])
                self.assertFalse(result["boundary"]["first_ordinate_zero"])
                self.assertTrue(
                    result["boundary"][
                        "coprime_factor_obstruction_to_published_rank_one_bound"
                    ]
                )

    def test_published_coefficient_polynomials(self):
        result = ttl.published_example(0)
        auxiliary = result["auxiliary"]
        self.assertEqual(auxiliary["delta1"], -109739)
        self.assertEqual(auxiliary["delta2"], -17606)
        self.assertEqual(auxiliary["s1"], 2304519)
        self.assertEqual(auxiliary["s2"], -2711324)

        b_at_zero = result["lift"]["b"]
        b_at_one = ttl.published_example(1)["lift"]["b"]
        self.assertEqual(b_at_zero, -1792587436107314570824479)
        self.assertEqual(b_at_one - b_at_zero, 635728705996536026)

        plus = result["lift"]["factor_plus"]
        minus = result["lift"]["factor_minus"]
        self.assertEqual(plus, 8697969664620875680)
        self.assertEqual(minus, 8697963332447929000)

    def test_exact_reduction_and_factor_identities(self):
        result = ttl.published_example(181)
        source = result["source"]
        lift = result["lift"]
        p = source["prime"]
        self.assertEqual(lift["a"] % p, source["a"])
        self.assertEqual(lift["b"] % p, source["b"])
        for lifted, reduced in zip(lift["points"], source["points"], strict=True):
            self.assertEqual([coordinate % p for coordinate in lifted], reduced)
        self.assertEqual(
            lift["discriminant_term"],
            lift["factor_plus"] * lift["factor_minus"],
        )
        self.assertEqual(
            703 * (lift["factor_plus"] - lift["factor_minus"]),
            4 * lift["points"][0][1],
        )

    def test_plain_integer_and_construction_guards(self):
        with self.assertRaisesRegex(TypeError, "plain integer"):
            ttl.published_example(True)
        with self.assertRaisesRegex(ValueError, "odd"):
            ttl.build_lift(
                prime=353,
                source_a=-1,
                source_b=16,
                t1=702,
                t2=439,
                b1=-21,
                b2=154,
                parameter_n=0,
            )
        with self.assertRaisesRegex(ValueError, "source curve"):
            ttl.build_lift(
                prime=353,
                source_a=-1,
                source_b=17,
                t1=703,
                t2=439,
                b1=-21,
                b2=154,
                parameter_n=0,
            )

    def test_coprime_factors_do_not_supply_rank_one_support(self):
        for parameter_n in (-1793, 181):
            lift = ttl.published_example(parameter_n)["lift"]
            self.assertGreater(lift["factor_plus"], 1)
            self.assertGreater(lift["factor_minus"], 1)
            self.assertEqual(
                math.gcd(lift["factor_plus"], lift["factor_minus"]), 1
            )


if __name__ == "__main__":
    unittest.main()
