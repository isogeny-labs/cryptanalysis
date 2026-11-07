"""Deterministic correctness controls, never a timed ECC benchmark."""
from itertools import combinations
import unittest

from sympy import expand, symbols

from pair_index import PairIndex, evaluate_many, pair_factor, signed_witnesses
from signed_labels import recover_signed_labels


class CurveFixture:
    p, a, b, order = 827, 1, 15, 823
    generator = (2, 822)

    def neg(self, point):
        return None if point is None else (point[0], -point[1] % self.p)

    def add(self, point, other):
        if point is None:
            return other
        if other is None:
            return point
        x, y = point
        u, v = other
        if x == u and (y+v) % self.p == 0:
            return None
        slope = ((3*x*x+self.a)*pow(2*y % self.p, -1, self.p) if point == other
                 else (v-y)*pow((u-x) % self.p, -1, self.p)) % self.p
        z = (slope*slope-x-u) % self.p
        return z, (slope*(x-z)-y) % self.p

    def mul(self, scalar, point=None):
        point = self.generator if point is None else point
        if scalar < 0:
            return self.mul(-scalar, self.neg(point))
        total = None
        while scalar:
            if scalar & 1:
                total = self.add(total, point)
            scalar >>= 1
            if scalar:
                point = self.add(point, point)
        return total


class PairIndexTests(unittest.TestCase):
    def setUp(self):
        self.curve = CurveFixture()
        self.vertices = [self.curve.mul(k) for k in (2, 7, 16, 27, 45, 63, 90)]
        self.index = PairIndex(self.curve.p, self.curve.a, self.curve.b, [r[0] for r in self.vertices])

    def test_symbolic_cleared_addition_identity(self):
        x, y, z, u, v, a, b = symbols('x y z u v a b')
        d = (x-y)**2
        f = d*z*z-2*((x+y)*(x*y+a)+2*b)*z+(x*y-a)**2-4*b*(x+y)
        lhs = (d*(z+x+y)-(u+v)**2)*(d*(z+x+y)-(u-v)**2)-d*f
        cu = u*u+x**3+a*x+b-2*v*v-2*d*(z+x+y)
        cv = v*v+y**3+a*y+b-2*(x**3+a*x+b)-2*d*(z+x+y)
        certificate = cu*(u*u-x**3-a*x-b)+cv*(v*v-y**3-a*y-b)
        self.assertEqual(expand(lhs-certificate), 0)

    def test_all_pair_factors_and_exact_coverage(self):
        roots = set()
        self.assertIsNone(self.curve.mul(self.curve.order))
        for i, j in combinations(range(len(self.vertices)), 2):
            left, right = self.vertices[i], self.vertices[j]
            plus = self.curve.add(left, right)
            minus = self.curve.add(left, self.curve.neg(right))
            factor = pair_factor(self.curve.p, self.curve.a, self.curve.b, left[0], right[0])
            self.assertEqual(int(factor(plus[0])), 0)
            self.assertEqual(int(factor(minus[0])), 0)
            roots.update((plus[0], minus[0]))
        self.assertEqual(self.index.polynomial.degree(), 42)
        self.assertEqual(self.index.coverage_size(), len(roots))

    def test_batch_localization_matches_complete_point_control(self):
        targets = [self.curve.mul(k) for k in range(1, self.curve.order)]
        actual = self.index.match_many([t[0] for t in targets])
        for point, matches in zip(targets, actual):
            expected = []
            for i, j in self.index.pairs:
                ri, rj = self.vertices[i], self.vertices[j]
                if point[0] in (self.curve.add(ri, rj)[0],
                                self.curve.add(ri, self.curve.neg(rj))[0]):
                    expected.append((i, j))
            self.assertEqual(sorted(matches), expected)
        repeated = [targets[0][0], targets[0][0], targets[7][0]]
        self.assertEqual(evaluate_many(self.index.polynomial, repeated, self.curve.p),
                         [int(self.index.polynomial(x)) for x in repeated])

    def test_full_witness_graph_and_label_replay(self):
        secret, order = 23, self.curve.order
        targets = [self.curve.mul(k) for k in range(order)]
        labels = [((k-(k*k+3)*secret) % order, (k*k+3) % order)
                  for k in range(order)]
        out = signed_witnesses(self.index, self.vertices, targets, labels, order,
                               self.curve.add, self.curve.neg)
        self.assertEqual(out['identity_targets'][0]['candidate_d'], secret)
        recovered = recover_signed_labels(len(self.vertices), out['edges'], order)
        self.assertEqual(len(recovered['labels']), len(self.vertices))
        q = self.curve.mul(secret)
        for i, (a, b) in recovered['labels'].items():
            self.assertEqual(self.curve.add(self.curve.mul(a), self.curve.mul(b, q)),
                             self.vertices[i])
        for a, b in recovered['zero_relation_certificates']:
            self.assertEqual((a+b*secret) % order, 0)

    def test_actual_seven_root_coset_is_filtered_to_curve_points(self):
        ambient = [x for x in range(self.curve.p) if pow(x, 7, self.curve.p) == 1]
        vertices = []
        for x in ambient:
            ys = [y for y in range(self.curve.p) if y*y % self.curve.p == (x**3+self.curve.a*x+self.curve.b) % self.curve.p]
            if ys:
                point = (x, ys[0])
                self.assertIsNone(self.curve.mul(self.curve.order, point))
                vertices.append(point)
        self.assertEqual(len(ambient), 7)
        self.assertGreaterEqual(len(vertices), 2)
        idx = PairIndex(self.curve.p, self.curve.a, self.curve.b, [point[0] for point in vertices])
        targets = [self.curve.mul(k) for k in range(1, self.curve.order)]
        matches = idx.match_many([t[0] for t in targets])
        self.assertEqual(sum(bool(row) for row in matches), 2*idx.coverage_size())

    def test_invalid_or_unsupported_index_inputs_refused(self):
        with self.assertRaises(ValueError):
            PairIndex(211, 0, 7, [3, 3])
        with self.assertRaises(ValueError):
            PairIndex(5, 1, 1, [0, 1, 2]).coverage_size()
        with self.assertRaises(ValueError):
            signed_witnesses(self.index, self.vertices[:-1], [], [], self.curve.order,
                             self.curve.add, self.curve.neg)


class SignedCycleTests(unittest.TestCase):
    def test_unbalanced_even_cycle_recovers_without_anchor(self):
        # Three sum edges and one difference edge: cycle multiplier is -1.
        edges = [(0, 1, 1, (8, 4)), (1, 2, 1, (12, 8)),
                 (2, 3, 1, (18, 12)), (3, 0, -1, (10, 8))]
        recovered = recover_signed_labels(4, edges, 101)
        expected = {0: (2, 0), 1: (6, 4), 2: (6, 4), 3: (12, 8)}
        self.assertEqual(recovered['labels'], expected)

    def test_balanced_even_cycle_needs_anchor(self):
        edges = [(0, 1, 1, (8, 4)), (1, 2, 1, (12, 8)),
                 (2, 3, 1, (18, 12)), (3, 0, 1, (14, 8))]
        self.assertEqual(recover_signed_labels(4, edges, 101)['labels'], {})
        self.assertEqual(len(recover_signed_labels(4, edges, 101,
                                                  {0: (2, 0)})['labels']), 4)

    def test_difference_cycles_keep_root_free(self):
        edges = [(0, 1, -1, (5, 3)), (1, 2, -1, (7, 9)),
                 (2, 0, -1, (-12, -12))]
        self.assertEqual(recover_signed_labels(3, edges, 101)['labels'], {})

    def test_cycle_defect_is_dlp_certificate(self):
        secret = 23
        edges = [(0, 1, 1, (8, 4)), (1, 2, 1, (12, 8)),
                 (2, 3, 1, (18, 12)), (3, 0, -1, (10, 8)),
                 (0, 1, 1, ((8-secret) % 101, 5))]
        certificates = recover_signed_labels(4, edges, 101)['zero_relation_certificates']
        self.assertTrue(certificates)
        for a, b in certificates:
            self.assertEqual((a+b*secret) % 101, 0)
        useful = [(a, b) for a, b in certificates if b]
        self.assertTrue(useful)
        self.assertEqual(-useful[0][0]*pow(useful[0][1], -1, 101) % 101, secret)


if __name__ == '__main__':
    unittest.main()
