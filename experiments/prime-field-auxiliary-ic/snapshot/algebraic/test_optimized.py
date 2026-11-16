import random
import unittest

from resultant_solver import Curve,prepare,solve,chain_resultant,nmod_poly,product_tree
from native_candidates import ChainCandidates
from known_root_gcd import KnownRootGCD
from prepare import chain


def canonical(result):
    return {tuple(sorted(map(tuple,r))) for r in result['relations']}


class OptimizedTests(unittest.TestCase):
    def test_block_gcd_exact_and_degenerate(self):
        p=127;xs=list(range(101));plan=KnownRootGCD(xs,p,13)
        rng=random.Random(723)
        polynomials=[nmod_poly([],p),nmod_poly([1],p),plan.polynomial,
                     plan.polynomial**2,nmod_poly([-126,1],p)]
        polynomials += [nmod_poly([rng.randrange(p) for _ in range(230)],p) for _ in range(8)]
        for R in polynomials:
            expected={int(x) for x,_ in plan.polynomial.gcd(R).roots()}
            self.assertEqual(plan.candidates(R),expected)
        with self.assertRaises(ValueError):KnownRootGCD([1,1],p)
        with self.assertRaises(ValueError):plan.candidates(nmod_poly([1],131))
        aux,V=chain(p,4,enumerate_all=True)
        model=prepare(dict(p=p,a=2,b=51),auxiliary=aux,roots=V)
        plan=KnownRootGCD(V,p,3);E=Curve(p,a4=2,a6=51)
        for x in [1,2,5]:
            R=E.point(x)
            if R:self.assertEqual(canonical(solve(model,R,root_plan=plan)),canonical(solve(model,R)))
        with self.assertRaises(ValueError):solve(model,E.point(1),root_plan=KnownRootGCD([1,2],p))

    def test_native_exact_values_and_relations_both_fields(self):
        for bits in [31,61]:
            p=2**bits-1;aux,V=chain(p,4,enumerate_all=True)
            curve=dict(p=p,a=2,b=14);model=prepare(curve,auxiliary=aux,roots=V)
            E=Curve(p,a4=2,a6=14);native=ChainCandidates(model,V)
            # Every signed finite factor-base pair plus independent targets.
            F=list(native.points.values());targets=set()
            for P in F:
                for Q in F:
                    for signed in [Q,E.neg(Q)]:
                        R=E.add(P,signed)
                        if R:targets.add(R)
            for x in range(1,15):
                P=E.point(x)
                if P:targets.add(P)
            for R in targets:
                candidates=native.candidates(R[0]);poly=chain_resultant(model,R)
                self.assertEqual(native.values(),[int(poly(x)) for x in native.xs])
                self.assertEqual(candidates,{x for x in native.xs if not poly(x)})
                self.assertEqual(canonical(native.solve(R)),canonical(solve(model,R)))
            native.close()
            with self.assertRaises(RuntimeError):native.candidates(1)
            with self.assertRaises(ValueError):ChainCandidates(model,V[:-1])
            with self.assertRaises(ValueError):ChainCandidates(model,V+[V[0]])

    def test_independent_native_handles(self):
        p=2**31-1;aux,V=chain(p,4,enumerate_all=True)
        models=[prepare(dict(p=p,a=a,b=b),auxiliary=aux,roots=V) for a,b in [(2,14),(0,3)]]
        handles=[ChainCandidates(m,V) for m in models]
        for _ in range(2):
            for model,handle in zip(models,handles):
                E=Curve(p,a4=model.curve['a'],a6=model.curve['b']);R=E.point(1)
                handle.candidates(R[0]);poly=chain_resultant(model,R)
                self.assertEqual(handle.values(),[int(poly(x)) for x in handle.xs])
        for handle in handles:handle.close()

    def test_liftable_gcd_every_finite_target_including_two_torsion(self):
        p=127;aux,V=chain(p,4,enumerate_all=True)
        for a,b in [(2,51),(0,1)]:
            model=prepare(dict(p=p,a=a,b=b),auxiliary=aux,roots=V)
            plan=KnownRootGCD.for_model(model,V,3);E=Curve(p,a4=a,a6=b)
            for x in range(p):
                rhs=(x**3+a*x+b)%p;y=pow(rhs,(p+1)//4,p)
                if y*y%p!=rhs:continue
                self.assertEqual(canonical(solve(model,(x,y),root_plan=plan)),canonical(solve(model,(x,y))))
        wrong=prepare(dict(p=p,a=2,b=51),auxiliary=aux,roots=V)
        with self.assertRaises(ValueError):solve(wrong,Curve(p,a4=2,a6=51).point(1),root_plan=plan)


if __name__=='__main__':unittest.main()
