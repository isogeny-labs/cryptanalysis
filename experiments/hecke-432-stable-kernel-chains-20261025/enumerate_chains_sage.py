"""Enumerate rational cyclic 16- and 27-isogeny chains from one source."""
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent


def linear_root(poly):
    assert poly.degree()==1
    return -poly[0]/poly[1]


def paths(curve, ell, depth, back_root=None, prefix=()):
    if depth==0:
        yield prefix
        return
    field=curve.base_field()
    x=PolynomialRing(field,'x').gen()
    for r,_ in curve.division_polynomial(ell).roots():
        if back_root is not None and r==back_root:
            continue
        phi=curve.isogeny(x-r)
        assert phi.degree()==ell
        dual=phi.dual()
        assert dual.degree()==ell
        next_back=linear_root(dual.kernel_polynomial())
        edge={'kernel_x':int(r),
              'source_j':int(curve.j_invariant()),
              'target_j':int(phi.codomain().j_invariant()),
              'target_ainvs':[int(c) for c in phi.codomain().ainvs()],
              'dual_kernel_x':int(next_back)}
        yield from paths(phi.codomain(),ell,depth-1,next_back,prefix+(edge,))


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_CHAIN_PROBE'
    F=GF(protocol['prime'])
    E=EllipticCurve(F,protocol['source_curve_ainvs'])
    assert E.j_invariant()==protocol['source_curve_j']
    out={'status':'COMPLETE_RATIONAL_CHAIN_PROBE','source_j':int(E.j_invariant()),
         'source_curve_order':int(E.cardinality()),'chains':{}}
    for ell,depth in ((2,4),(3,3)):
        found=list(paths(E,ell,depth))
        out['chains'][str(ell)]={'length':depth,'count':len(found),'paths':found}
        print(f'ell={ell} depth={depth} paths={len(found)}',flush=True)
    out['paired_chain_count']=out['chains']['2']['count']*out['chains']['3']['count']
    (HERE/'chain_probe.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'paired_chain_count':out['paired_chain_count']},sort_keys=True))


if __name__=='__main__':
    main()
