"""Derive j(3 tau) and j(9 tau) on X0(27)=27a1 by q-series interpolation."""
import json
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, QQ, matrix
from sage.modular.modform.j_invariant import j_invariant_qexp

HERE=Path(__file__).resolve().parent


def basis(x,y,bound):
    return [(a,b,x**a*y**b) for b in (0,1)
            for a in range((bound-3*b)//2+1)]


def derive(x,y,j,pole,bound):
    aa=basis(x,y,bound)
    bb=basis(x,y,bound+pole)
    series=[f*j for _,_,f in aa]+[f for _,_,f in bb]
    lo,hi=-(bound+pole),100
    mat=matrix(QQ,[[s[k] for s in series] for k in range(lo,hi)])
    kernel=mat.right_kernel()
    assert kernel.dimension()==1,(pole,bound,kernel.dimension())
    v=kernel.basis()[0]
    combo=sum(v[k]*s for k,s in enumerate(series))
    assert all(combo[k]==0 for k in range(100,150))
    def terms(group,offset):
        return [{'x_power':a,'y_power':b,'coefficient':str(v[offset+k])}
                for k,(a,b,_) in enumerate(group) if v[offset+k]]
    return {'denominator':terms(aa,0),'numerator':terms(bb,len(aa)),
            'denominator_pole_at_infinity':bound,'j_pole_at_infinity':pole,
            'q_training_exponents':[lo,hi-1],
            'q_holdout_exponents':[100,149],
            'training_nullity':1,'holdout_zero':True,
            'identity_form':'denominator*j + numerator = 0'}


def main():
    C=EllipticCurve('27a1')
    x,y=C.modular_parametrization().power_series(230)
    q=x.parent().gen()
    out={'curve_ainvs':[int(a) for a in C.a_invariants()]}
    for k,pole,bound in ((3,3,33),(9,9,27)):
        small=j_invariant_qexp(180//k+3)
        jk=sum(small[n]*q**(k*n) for n in range(-1,180//k+1))
        out[f'j{k}']=derive(x,y,jk,pole,bound)
        print(json.dumps({'k':k,'denominator_terms':len(out[f'j{k}']['denominator']),
                          'numerator_terms':len(out[f'j{k}']['numerator'])}),flush=True)
    (HERE/'intermediate_j.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':
    main()
