"""Independent small-group controls for collision-relation certificates."""
import copy
import unittest
from modular import Curve
from pair_reuse import Basis,combine,harvest,check_index


class PairReuseTests(unittest.TestCase):
    def test_sparse_coefficients_and_independence(self):
        self.assertEqual(combine({0:1,1:2},{0:1,2:3},-1),{1:2,2:-3})
        basis=Basis(11)
        self.assertTrue(basis.add({0:1,1:2}))
        self.assertFalse(basis.add({0:2,1:4}))
        self.assertTrue(basis.add({1:1}))

    def test_relations_from_known_five_torsion(self):
        curve=Curve(367)
        # P and 2P are separate unknown labels. Pair collisions reveal their ratio.
        base=[(5,5),(16,306)]
        index,result=harvest(base,curve,5)
        self.assertEqual(result['pair_construction_group_additions'],15)
        self.assertEqual(len(index),5)
        self.assertEqual(result['independent_collision_rank'],1)
        self.assertGreater(result['coefficient_zero_identities'],0)
        self.assertEqual(check_index(base,5,result,367)['status'],'independently_verified')
        damaged=copy.deepcopy(result)
        damaged['basis_witnesses'][0]['row']={0:1}
        with self.assertRaises(AssertionError):check_index(base,5,damaged,367)


if __name__=='__main__':unittest.main()
