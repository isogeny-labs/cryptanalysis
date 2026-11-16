"""Independent polynomial checks for centered, padded SIMD circuit evaluation."""
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from resultant_solver import prepare,chain_resultant,Curve,solve
from native_candidates import ChainCandidates
from prepare import chain


def canonical(result):return {tuple(sorted(map(tuple,r))) for r in result['relations']}


class FusedTests(unittest.TestCase):
    def test_exact_values_and_signed_relations_both_fields(self):
        count=0
        for bits,a,b in [(31,2,14),(61,0,3)]:
            p=2**bits-1;E=Curve(p,a4=a,a6=b)
            for depth in [1,3,5]:
                aux,V=chain(p,depth,enumerate_all=True)
                model=prepare(dict(p=p,a=a,b=b),auxiliary=aux,roots=V)
                current=ChainCandidates(model,V,native_source=ROOT/'native_v2.cpp')
                previous=ChainCandidates(model,V)
                targets={E.point(x) for x in range(1,15)}
                F=list(current.points.values())
                for P in F:
                    for Q in F:
                        targets.add(E.add(P,Q));targets.add(E.add(P,E.neg(Q)))
                targets.discard(None)
                for R in targets:
                    self.assertEqual(current.candidates(R[0]),previous.candidates(R[0]))
                    poly=chain_resultant(model,R)
                    self.assertEqual(current.values(),[int(poly(x)) for x in current.xs])
                    self.assertEqual(current.values(),previous.values())
                    self.assertEqual(canonical(current.solve(R)),canonical(solve(model,R)))
                    count+=1
                current.close();previous.close()
        print('Exact native v2 target checks:',count)

    def test_nonzero_first_shift_and_equivalent_terminal(self):
        # Change the intermediate coordinate by a nonzero translation. This
        # exercises the initial shift, rather than only the convenient r0=0.
        p=2**31-1;aux,V=chain(p,3,enumerate_all=True)
        shifted={**aux,'maps':[dict(m) for m in aux['maps']]}
        r=17;shifted['maps'][0]['r']=r
        shifted_roots=[(x+r)%p for x in V]
        shifted['terminal_c']-=p
        model=prepare(dict(p=p,a=2,b=14),auxiliary=shifted,roots=shifted_roots)
        current=ChainCandidates(model,shifted_roots,native_source=ROOT/'native_v2.cpp')
        E=Curve(p,a4=2,a6=14)
        for x in range(1,25):
            R=E.point(x);current.candidates(R[0]);poly=chain_resultant(model,R)
            self.assertEqual(current.values(),[int(poly(v)) for v in current.xs])
        current.close()


if __name__=='__main__':unittest.main(verbosity=2)
