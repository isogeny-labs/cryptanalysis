"""Fixed-fixture unit controls; no timing panel or newly sampled instances."""
import unittest
from core import Curve, oracle, add_row, rho
from systems import build, solve
from analyze import summarize


class FixedFixtureTests(unittest.TestCase):
    def setUp(self):
        self.C = Curve(101, 17, 1)
        self.base = [(13, 29), (19, 17)]
        for P in self.base:
            self.assertTrue(self.C.contains(P))
            self.assertIsNone(self.C.mul(13, P))

    def test_planted_and_cancelled_sums_all_models(self):
        P, Q = self.base
        targets = [self.C.add(self.C.add(P, P), Q), Q]
        expected = oracle(self.C, self.base)
        for R in targets:
            for model in ['montgomery', 'edwards', 'invariant', 'retained']:
                with self.subTest(target=R, model=model):
                    self.assertEqual(set(map(tuple, solve(self.C, self.base, R, model)['rows'])),
                                     expected.get(R, set()))

    def test_infinity_branch_present(self):
        R = self.base[0]
        _, _, _, infinity = build(self.C, self.base, R, 'retained')
        self.assertIn((R[0], R[0], R[0]), infinity)

    def test_unsatisfiable_one_point_base(self):
        base = self.base[:1]
        R = self.C.mul(2, base[0])
        self.assertNotIn(R, oracle(self.C, base))
        for model in ['montgomery', 'edwards', 'invariant', 'retained']:
            self.assertEqual(solve(self.C, base, R, model)['rows'], [])

    def test_same_point_rho_fixture(self):
        G = self.base[0]
        Q = self.C.mul(7, G)
        result = rho(self.C, 13, G, Q)
        self.assertEqual(result['status'], 'self_checked_recovered')
        self.assertEqual(result['scalar'], 7)

    def test_censoring_is_not_zero_cost_or_complete(self):
        item = {'instance': {'fixture_id': 'fixture', 'source_field': 101,
                              'p': 101, 'r': 13, 'kind': 'torsion'},
                'arm': 'montgomery', 'workload': {'seed': 1},
                'status': 'rank_incomplete', 'rank': 0, 'unknowns': 3,
                'queries': [{'status': 'timeout', 'pdp': {'wall_ns': 2000}}],
                'complete_collection_wall_ns': None}
        result = summarize(item)
        self.assertIsNone(result['pdp_ns_per_usable_relation'])
        self.assertIsNone(result['complete_collection_wall_ns'])
        self.assertEqual(result['query_timeout_rate'], 1)

    def test_rank_update_checks_dependency(self):
        pivots = {}
        self.assertTrue(add_row(pivots, [1, 2], 13, 1))
        self.assertFalse(add_row(pivots, [2, 4], 13, 1))
        with self.assertRaises(ValueError):
            add_row(pivots, [2, 5], 13, 1)


if __name__ == '__main__':
    unittest.main()
