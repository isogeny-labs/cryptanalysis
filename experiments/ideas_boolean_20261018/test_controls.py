import itertools
import random
import unittest
from collections import Counter

import run


class Controls(unittest.TestCase):
    def test_block_orders_really_eliminate(self):
        blocks=[[0,1],[2,3],[4,5]]
        first,_=run.order_layout(6,blocks,"block-eliminate-first-half")
        second,_=run.order_layout(6,blocks,"block-eliminate-second-half")
        self.assertGreater(first.index(1),first.index(60))
        self.assertGreater(second.index(4),second.index(3))
        natural,_=run.order_layout(6,blocks,"grevlex-natural")
        self.assertLess(natural.index(1),natural.index(60))

    def test_dinur_recursive_parity_and_complement_semantics(self):
        # At N=6,n1=3 lambda=1/5 gives n2=1: actual Algorithm 2
        # random-combination/interpolation/majority path, not base-only.
        equations=[{1,2,0},{2,4},{8,16},{16,32}]
        stats=Counter()
        output=run.dinur_mult_parity(equations,6,3,3,1,random.Random(20261018),stats)
        expected={y:sum(all(run.poly_eval(g,y | (z << 3)) == 0 for g in equations)
                        for z in range(8)) & 1 for y in range(8)}
        self.assertEqual(output,expected)
        self.assertGreater(stats["recursive_calls"],1)
        self.assertGreater(stats["random_coefficient_bits"],0)
        # The constant inconsistent equation must have no solutions.
        self.assertEqual(run.dinur_mult_parity([{0}],3,1,2,0,random.Random(1),Counter()),
                         {y:0 for y in range(4)})

    def test_trace_self_replay_and_divergence_fallback(self):
        rows=[7,6,3,0]
        original,_,trace=run.eliminate(rows)
        replay,stats,_=run.eliminate(rows,trace)
        self.assertEqual(original,replay)
        self.assertIsNone(stats["divergence_row"])
        failed,stats,_=run.eliminate([1,6,3,0],trace)
        self.assertIsNone(failed)
        self.assertIsNotNone(stats["divergence_row"])

    def test_exact_order_certificate_rejects_wrong_ideal(self):
        for order in ["grevlex-natural","block-eliminate-first-half","weighted-grevlex"]:
            engine=run.OrderedF5(3,[[0],[1],[2]],order,timeout=10,max_pairs=10000)
            certificate=run.certify_order([[1,0]],[[1,0]],engine)
            self.assertTrue(certificate["verified"])
            certificate=run.certify_order([[1,0]],[[1]],engine)
            self.assertFalse(certificate["verified"])


if __name__ == "__main__":
    unittest.main()
