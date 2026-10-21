import unittest
from itertools import product

from orbit_core import m3_truths, mobius_anf, model, planted_targets, quotient_basis, slot_sets


class OrbitQuotientTests(unittest.TestCase):
    def test_pair_index_matches_direct_triple_enumeration(self):
        # Independent small-modulus check of the algorithmic bridge formalized
        # by lean/OrbitPairIndex.lean, for both representative policies.
        M = {"r": 11, "s": 2, "keys": [1, 2], "scalars": {1: 1, 2: 3},
             "lam": 2, "H": [1, 10]}
        targets = list(range(M["r"]))
        for mode in ("fixed", "orbit"):
            truths, _ = m3_truths(M, targets, mode)
            slots = slot_sets(M, 3, mode, (0, 1, 2))
            for a, b, c in product(M["keys"], repeat=3):
                mask = a | (b << M["s"]) | (c << (2 * M["s"]))
                sums = {(x + y + z) % M["r"] for x, y, z in
                        product(slots[0][a], slots[1][b], slots[2][c])}
                for target, truth in zip(targets, truths):
                    self.assertEqual(bool(truth[mask]), target in sums)

    def test_payload_basis_shape(self):
        self.assertEqual(len(quotient_basis(13, 4)), 4)
        self.assertEqual(len(quotient_basis(19, 6)), 6)

    def test_n13_reference(self):
        M = model(13, 4, 5475)
        self.assertEqual(M["r"], 2003)
        self.assertEqual(M["lam"], 89)
        self.assertEqual(len(M["keys"]), 7)
        self.assertEqual(len(M["H"]), 26)

        targets, _ = planted_targets(M, 3, 1, (0, 1, 2), 20260926)
        fixed, fs = m3_truths(M, targets, "fixed")
        orbit, os = m3_truths(M, targets, "orbit")
        self.assertEqual(fs[0]["positive_key_tuples"], 3)
        self.assertEqual(os[0]["positive_key_tuples"], 330)
        self.assertEqual(mobius_anf(fixed[0], 12)["degree"], 12)
        self.assertEqual(mobius_anf(orbit[0], 12)["degree"], 11)

    def test_n19_reference(self):
        M = model(19, 6, 112679)
        self.assertEqual(M["r"], 130873)
        self.assertEqual(M["lam"], 41811)
        self.assertEqual(len(M["keys"]), 23)
        self.assertEqual(len(M["H"]), 38)

        targets, _ = planted_targets(M, 3, 1, (0, 1, 2), 20260926)
        fixed, fs = m3_truths(M, targets, "fixed")
        orbit, os = m3_truths(M, targets, "orbit")
        self.assertEqual(fs[0]["positive_key_tuples"], 1)
        self.assertEqual(os[0]["positive_key_tuples"], 3895)
        self.assertEqual(mobius_anf(fixed[0], 18)["degree"], 18)
        self.assertEqual(mobius_anf(orbit[0], 18)["degree"], 18)


if __name__ == "__main__":
    unittest.main()
