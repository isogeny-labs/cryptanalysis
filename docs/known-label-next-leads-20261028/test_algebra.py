"""Algebra and abstract-group correctness controls; no ECDLP benchmark."""
import itertools
import unittest
import sympy as sp
from label_graph import recover_labels, prony_parameters


class AlgebraChecks(unittest.TestCase):
    def test_triangle_and_prony_identities_symbolically(self):
        a, b, c = sp.symbols('a b c')
        s1, s2, s3 = a+b-c, a*a+b*b-c*c, a**3+b**3-c**3
        identities = [2*a-((a+b)-(b+c)+(c+a)),
                      s1*s1-s2-2*(a-c)*(b-c),
                      -s1**3+3*s1*s2-2*s3-6*c*(a-c)*(b-c),
                      2*a*b-(s1*s1-s2+2*c*s1)]
        self.assertTrue(all(sp.expand(x) == 0 for x in identities))

    def test_prony_all_distinct_small_index_signatures(self):
        signatures = set()
        for triple in itertools.combinations(range(7), 3):
            for negative in triple:
                i, j = [x for x in triple if x != negative]
                k = negative
                moments = tuple((i**m+j**m-k**m) % 101 for m in (1, 2, 3))
                self.assertNotIn(moments, signatures)
                signatures.add(moments)
                self.assertEqual(prony_parameters(*moments, 101),
                                 (k, (i+j) % 101, i*j % 101))
        self.assertEqual(len(signatures), 105)

    def test_cross_sign_family_independence_is_not_assumed(self):
        positive = tuple(sum(x**m for x in (0, 1, 2)) % 11 for m in range(4))
        mixed = tuple((3**m+10**m-1**m) % 11 for m in range(4))
        self.assertEqual(positive, tuple(3*x % 11 for x in mixed))

    def test_triangle_recovers_individual_labels(self):
        labels = [(7, 3), (12, 8), (30, 4)]
        edges = [(i, j, tuple((labels[i][k]+labels[j][k]) % 101 for k in (0, 1)))
                 for i, j in [(0, 1), (1, 2), (2, 0)]]
        result = recover_labels(3, edges, 101)
        self.assertEqual(result['labels'], dict(enumerate(labels)))
        self.assertEqual(result['zero_relation_certificates'], [])

    def test_bipartite_component_requires_anchor(self):
        edges = [(0, 1, (10, 5)), (1, 2, (18, 9))]
        self.assertEqual(recover_labels(3, edges, 101)['labels'], {})
        result = recover_labels(3, edges, 101, {0: (2, 1)})
        self.assertEqual(result['labels'], {0: (2, 1), 1: (8, 4), 2: (10, 5)})

    def test_cycle_label_defect_is_a_dlp_certificate(self):
        order, secret = 101, 23
        logs = [7, 12, 30, 45]
        edges = []
        for (i, j), v in zip([(0, 1), (1, 2), (2, 3), (3, 0)], [1, 2, 3, 5]):
            edges.append((i, j, ((logs[i]+logs[j]-v*secret) % order, v)))
        result = recover_labels(4, edges, order)
        certificates = result['zero_relation_certificates']
        self.assertTrue(certificates)
        for u, v in certificates:
            self.assertEqual((u+v*secret) % order, 0)
            if v:
                self.assertEqual(-u*pow(v, -1, order) % order, secret)


if __name__ == '__main__':
    unittest.main(verbosity=2)
