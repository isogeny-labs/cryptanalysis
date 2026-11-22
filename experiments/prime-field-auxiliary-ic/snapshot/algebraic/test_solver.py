"""Meaningful checks against exhaustive point-sum oracles on small bases."""
import itertools
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from solver import Curve,ROOT,make_system,solve,validate_solution
from prepare import chain


def lifted(E,roots):
    points=[]
    for x in roots:
        rhs=(x**3+E.a4*x+E.a6)%E.p
        y=pow(rhs,(E.p+1)//4,E.p)
        if y*y%E.p==rhs:
            points.extend([(x,y)] if y==0 else [(x,y),(x,-y%E.p)])
    return points


def oracle(E,points,target,m):
    result=set()
    for choices in itertools.product(points,repeat=m):
        total=None
        for P in choices:total=E.add(total,P)
        if total==target:result.add(tuple(sorted(choices)))
    return result


class AlgebraicSolverTests(unittest.TestCase):
    def compare(self,bits,m,depth,summation='split'):
        curve=dict(p=2**bits-1,a=2 if bits==31 else 0,b=14 if bits==31 else 3)
        aux,V=chain(curve['p'],depth,enumerate_all=True)
        E=Curve(curve['p'],a4=curve['a'],a6=curve['b'])
        points=lifted(E,V)
        positive=[P for P in points if P[1]<=E.p-P[1]]
        # Use a nontrivial regular sum, without cancelling a +/- pair.
        selected=[positive[j%len(positive)] for j in range(m)]
        target=None
        for P in selected:target=E.add(target,P)
        self.assertIsNotNone(target)
        expected=oracle(E,points,target,m)
        self.assertTrue(expected)
        for encoding in ['chain','expanded']:
            system=make_system(curve,target,m=m,auxiliary=aux,roots=V,encoding=encoding,summation=summation)
            result=solve(system,ROOT/'tests'/f'{bits}_m{m}_s{depth}_{encoding}',timeout=20)
            self.assertEqual(result['status'],'solved',result)
            found={tuple(sorted(tuple(P) for P in relation)) for relation in result['relations']}
            self.assertEqual(found,expected)
            self.assertTrue(all(validate_solution(system,s) is not None for s in result['solutions']))

    def test_two_sum_31bit_and_integer_overflow_regression(self):self.compare(31,2,3)
    def test_three_sum_31bit(self):self.compare(31,3,3)
    def test_two_sum_61bit_exact_modular_coefficients(self):self.compare(61,2,3)
    def test_three_sum_61bit(self):self.compare(61,3,3)
    def test_direct_S4_31bit(self):self.compare(31,3,2,'direct')
    def test_direct_S4_61bit(self):self.compare(61,3,2,'direct')

    def test_direct_S4_handles_infinite_intermediate_sum(self):
        E=Curve(127,a4=1)
        curve=dict(p=127,a=1,b=0);roots=[0,1,3];target=(0,0)
        system=make_system(curve,target,m=3,roots=roots,encoding='plain',summation='direct')
        result=solve(system,ROOT/'tests/infinite_intermediate',timeout=10)
        self.assertEqual(result['status'],'solved',result)
        actual={tuple(sorted(tuple(P) for P in rel)) for rel in result['relations']}
        self.assertEqual(actual,oracle(E,lifted(E,roots),target,3))
        self.assertIn(((0,0),(0,0),(0,0)),actual)

    def test_split_S4_completes_missing_infinity_chart(self):
        curve=dict(p=127,a=1,b=0);target=(0,0)
        system=make_system(curve,target,m=3,roots=[0],encoding='plain',summation='split')
        result=solve(system,ROOT/'tests/split_infinity_regression',timeout=10)
        self.assertEqual(result['status'],'solved',result)
        self.assertTrue(result['split_complete'])
        self.assertTrue(result['infinity_chart_required'])
        self.assertEqual(result['relations'],[[[0,0],[0,0],[0,0]]])

    def test_ordinary_benchmark_base_independent_of_target(self):
        from benchmark_relations import build_case
        curve=dict(p=127,a=2,b=51)
        E=Curve(127,a4=2,a6=51)
        first,second=E.point(80),E.point(100)
        with patch('benchmark_relations.uniform_finite_point',return_value=first):
            a=build_case(7,3,2,0,curve=curve)
        with patch('benchmark_relations.uniform_finite_point',return_value=second):
            b=build_case(7,3,2,1,curve=curve)
        self.assertEqual(a['ordinary_roots'],b['ordinary_roots'])
        self.assertEqual(a['structured_roots'],b['structured_roots'])
        self.assertEqual(a['ordinary_roots'],list(range(10,18)))
        self.assertNotIn(first[0],a['ordinary_roots'])
        self.assertNotIn(second[0],b['ordinary_roots'])
        self.assertTrue(a['bases_fixed_before_target'])
        self.assertFalse(a['planted_coordinates'])

    def test_large_curve_coefficient_no_machine_int_overflow(self):
        p=2**31-1;curve=dict(p=p,a=2,b=p-14)
        E=Curve(p,a4=2,a6=p-14)
        aux,V=chain(p,2)
        F=lifted(E,V)
        target=E.add(F[0],F[2] if len(F)>2 else F[0])
        self.assertIsNotNone(target)
        expected=oracle(E,F,target,2)
        result=solve(make_system(curve,target,m=2,auxiliary=aux,roots=V),ROOT/'tests/large_coefficient',timeout=10)
        self.assertEqual(result['status'],'solved',result)
        actual={tuple(sorted(tuple(P) for P in rel)) for rel in result['relations']}
        self.assertEqual(actual,expected)

    def test_unsatisfiable_and_denominator_handling(self):
        p=2**31-1;curve=dict(p=p,a=2,b=14);E=Curve(p,a4=2,a6=14)
        aux,V=chain(p,2)
        points=lifted(E,V)
        target=E.point(10)
        while oracle(E,points,target,2):target=E.point(target[0]+1)
        system=make_system(curve,target,m=2,auxiliary=aux,roots=V)
        result=solve(system,ROOT/'tests/unsatisfiable',timeout=10)
        self.assertEqual(result['status'],'solved',result)
        self.assertEqual(result['relations'],[])
        self.assertEqual(result['lex_basis'],['1'])
        # Cleared quadratic at a denominator zero becomes -B != 0.
        self.assertTrue(all(step['B']%p for step in aux['maps']))
        self.assertIsNone(validate_solution(system,{'x1':0,'x2':0,'z1j2':0,'z2j2':0}))

    def test_invalid_curve_and_mismatched_auxiliary_rejected(self):
        with self.assertRaises(ValueError):
            make_system(dict(p=127,a=0,b=0),(0,0),roots=[0,1],encoding='plain')
        aux,_=chain(127,2)
        with self.assertRaises(ValueError):
            make_system(dict(p=2**31-1,a=2,b=14),(1,814455902),auxiliary=aux)


if __name__=='__main__':unittest.main(verbosity=2)
