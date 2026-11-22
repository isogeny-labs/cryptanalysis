"""Independent checks of the structure-aware algebraic solver."""
import itertools
import unittest
import json
from collections import defaultdict

from resultant_solver import *
from prepare import chain
from benchmark_relations import uniform_finite_point


def finite_points(E,roots=None):
    result=[]
    for x in range(E.p) if roots is None else roots:
        rhs=(x**3+E.a4*x+E.a6)%E.p
        y=pow(rhs,(E.p+1)//4,E.p)
        if y*y%E.p==rhs:
            result.extend([(x,y)] if y==0 else [(x,y),(x,-y%E.p)])
    return result


def relation_set(result):
    return {tuple(sorted(tuple(P) for P in pair)) for pair in result['relations']}


class ResultantTests(unittest.TestCase):
    def test_full_polynomial_identity_three_independent_computations(self):
        for bits,a,b in [(7,2,51),(31,2,14),(61,0,3)]:
            curve=dict(p=2**bits-1,a=a,b=b);E=Curve(curve['p'],a4=a,a6=b)
            for depth in [1,2,3,5]:
                aux,V=chain(E.p,depth,enumerate_all=True)
                A=prepare(curve,auxiliary=aux);B=prepare(curve,roots=V,encoding='expanded')
                self.assertEqual(A.polynomial,B.polynomial)
                for seed in range(3):
                    T=uniform_finite_point(E,seed)
                    self.assertEqual(chain_resultant(A,T),explicit_resultant(B,T))
                    self.assertEqual(chain_resultant(A,T),chain_resultant_norm_reference(A,T))

    def exhaustive(self,a,b):
        curve=dict(p=127,a=a,b=b);E=Curve(127,a4=a,a6=b)
        aux,V=chain(127,3,enumerate_all=True)
        models=[prepare(curve,auxiliary=aux),prepare(curve,roots=V,encoding='expanded')]
        expected=defaultdict(set)
        for P,Q in itertools.product(finite_points(E,V),repeat=2):
            expected[E.add(P,Q)].add(tuple(sorted([P,Q])))
        for target in finite_points(E):
            for model in models:
                self.assertEqual(relation_set(solve(model,target)),expected[target],(a,b,target))

    def test_every_finite_target_prime_order_curve(self):self.exhaustive(2,51)
    def test_every_finite_target_auxiliary_curve_and_two_torsion(self):self.exhaustive(1,0)

    def test_positive_relations_in_both_requested_prime_fields(self):
        for bits,a,b in [(31,2,14),(61,0,3)]:
            curve=dict(p=2**bits-1,a=a,b=b);E=Curve(curve['p'],a4=a,a6=b)
            aux,V=chain(E.p,3,enumerate_all=True)
            points=[P for P in finite_points(E,V) if P[1]<=E.p-P[1]]
            target=E.add(points[0],points[1])
            expected={tuple(sorted([P,Q])) for P,Q in itertools.product(finite_points(E,V),repeat=2)
                      if E.add(P,Q)==target}
            self.assertTrue(expected)
            self.assertEqual(relation_set(solve(prepare(curve,auxiliary=aux),target)),expected)

    def test_lazy_auxiliary_setup_does_not_enumerate_factor_base(self):
        aux,V=chain(2**31-1,10,root_limit=0)
        self.assertEqual(V,[]);self.assertEqual(aux['roots_checked'],0)
        model=prepare(dict(p=2**31-1,a=2,b=14),auxiliary=aux)
        self.assertEqual(model.polynomial.degree(),1024)

    def test_complete_index_calculus_pipeline_without_pair_tables(self):
        from index_calculus import run
        public=json.loads((ROOT/'fixtures/toy_public.json').read_text())
        auxiliary=json.loads((ROOT/'fixtures/toy_auxiliary.json').read_text())
        for encoding,rootfile in [('chain','toy_roots.json'),('plain','toy_plain_roots.json')]:
            roots=json.loads((ROOT/'fixtures'/rootfile).read_text())
            for m in [2,3]:
                result=run(public,roots,auxiliary if encoding=='chain' else None,encoding,
                           ROOT/'full_toy'/f'resultant_{encoding}_m{m}',engine='resultant',m=m,
                           max_trials=100,total_timeout=10)
                self.assertEqual(result['status'],'solved',result)
                self.assertEqual(result['recovered'],37)
                self.assertTrue(result['verified'])

    def test_three_point_hybrid_against_exhaustive_oracle(self):
        curve=dict(p=127,a=2,b=51);E=Curve(127,a4=2,a6=51)
        aux,V=chain(127,3,enumerate_all=True)
        model=prepare(curve,auxiliary=aux);points=signed_base(model,V)
        expected=defaultdict(set)
        for P,Q,R in itertools.product(points,repeat=3):
            expected[E.add(E.add(P,Q),R)].add(tuple(sorted([P,Q,R])))
        for target in finite_points(E):
            answer=solve_three(model,target,points)
            self.assertEqual(bool(answer['relations']),bool(expected[target]))
            for rel in answer['relations']:
                self.assertIn(tuple(sorted(tuple(P) for P in rel)),expected[target])

    def test_mismatched_membership_and_degenerate_maps_rejected(self):
        curve=dict(p=127,a=2,b=51);aux,V=chain(127,3,enumerate_all=True)
        wrong=list(V);wrong[0]=(wrong[0]+1)%127
        with self.assertRaises(ValueError):prepare(curve,auxiliary=aux,roots=wrong)
        model=prepare(curve,auxiliary=aux)
        with self.assertRaises(ValueError):signed_base(model,wrong)
        bad=json.loads(json.dumps(aux));bad['maps'][0]['B']=0
        with self.assertRaises(ValueError):prepare(curve,auxiliary=bad)


if __name__=='__main__':unittest.main(verbosity=2)
