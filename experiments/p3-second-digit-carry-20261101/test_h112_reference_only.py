import unittest

import h112_reference_verify as reference


class H112ReferenceOnlyTests(unittest.TestCase):
    def test_frozen_predicates_are_complete_unique_and_non_low_only(self):
        specs = reference.PREDICATES
        self.assertEqual(len(specs), 144)
        self.assertEqual(len({item["id"] for item in specs}), 144)
        self.assertEqual(sum(item["family"] == "depth" for item in specs), 72)
        self.assertEqual(sum(item["family"] == "cross" for item in specs), 72)
        self.assertTrue(all(item.get("channel") != "low" for item in specs))

    def test_e101_group_orbit_and_public_half(self):
        curve = reference.CURVES["E101"]
        generator = (0, 3)
        points = reference.orbit(curve, generator)
        self.assertEqual(len(points), curve.r)
        target = points[37]
        half = curve.mul((curve.r + 1) // 2, target)
        self.assertEqual(curve.add(half, half), target)

    def test_p3_carry_has_two_bounded_digits(self):
        curve = reference.CURVES["E101"]
        target = curve.mul(37, (0, 3))
        half = curve.mul((curve.r + 1) // 2, target)
        low, high = reference.carry(curve, half, target)
        self.assertTrue(0 <= low < curve.p)
        self.assertTrue(0 <= high < curve.p)

    def test_stable_digest_excludes_only_runtime_metadata(self):
        left = {"value": [1, 2, 3], "total_elapsed_ns": 10, "environment": {"python": "a"}}
        right = {"value": [1, 2, 3], "total_elapsed_ns": 99, "environment": {"python": "b"}}
        self.assertEqual(reference.stable_digest(left), reference.stable_digest(right))
        right["value"][1] = 7
        self.assertNotEqual(reference.stable_digest(left), reference.stable_digest(right))


if __name__ == "__main__":
    unittest.main()
