"""Synthetic unit tests only: these do not execute the frozen research fixture."""
import unittest
from audit import Curve, dense_reduce, equality_rows, scalar_rows, check_rows


class CheckerTests(unittest.TestCase):
    def test_rational_five_torsion(self):
        curve = Curve()
        point = (5, 5)
        # Hand calculation: doubling slope is 5, so 2P=(16,-61).
        expected = [None, (5, 5), (16, 306), (16, 60), (5, 361), None]
        self.assertEqual([curve.mul(k, point) for k in range(6)], expected)
        self.assertEqual(curve.mul(-1, point), (5, 361))
        self.assertTrue(all(curve.contains(p) for p in expected))

    def test_elimination_and_affine_rhs(self):
        pivots, rows = dense_reduce([{0: 1, 1: 1, 2: 3}, {0: 1, 1: -1, 2: 1}], 3)
        self.assertEqual(pivots, [0, 1])
        self.assertEqual([row[2] for row in rows], [2, 1])
        self.assertEqual(len(dense_reduce([{0: 1}, {0: 2}], 2)[0]), 1)

    def test_collection_group_identities(self):
        curve = Curve()
        points = [None, (5, 5), (16, 306), (5, 5)]
        rows = equality_rows(points) + scalar_rows(points, curve, [2, 3])
        self.assertIn({3: 1, 1: -1}, rows)
        self.assertIn({2: 1, 1: -2}, rows)
        check_rows(rows, points, curve)
        with self.assertRaises(AssertionError):
            check_rows([{1: 1}], points, curve)


if __name__ == '__main__':
    unittest.main()
