"""Prove the lifted x_B relation by exact q expansion and pole degree."""
import json
from hashlib import sha256
from math import lcm
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, Infinity, QQ

HERE=Path(__file__).resolve().parent
SOURCE_PRECISION=1250
POLE_DEGREE_BOUND=1056


def main():
    reconstruction_path=HERE/'reconstruction.json'
    rec=json.loads(reconstruction_path.read_text())
    assert rec['status']=='PASS_RATIONAL_B_RECONSTRUCTION_WITH_HOLDOUT'
    terms=rec['terms']
    ratios=rec['coefficients_num_den']
    denominator=lcm(*(d for _,d in ratios))
    coefficients=[n*(denominator//d) for n,d in ratios]
    assert max(2*a+3*b+2*c for a,b,c in terms)==44
    assert max(48*a+72*b+48*c for a,b,c in terms)==POLE_DEGREE_BOUND
    C=EllipticCurve('27a1')
    B=EllipticCurve(QQ,[0,0,0,0,-16])
    xc,yc=C.modular_parametrization().power_series(SOURCE_PRECISION)
    xb,_=B.modular_parametrization().power_series(SOURCE_PRECISION)
    xcp=[xc**a for a in range(23)]
    xbp=[xb**c for c in range(13)]
    minimum_precision=min(int(s.prec()) for s in xcp+xbp+[yc]
                          if s.prec()!=Infinity)
    assert minimum_precision>POLE_DEGREE_BOUND
    total=xc.parent().zero()
    used=0
    for (a,b,c),coefficient in zip(terms,coefficients):
        if coefficient:
            value=coefficient*xcp[a]*(yc if b else xc.parent().one())*xbp[c]
            assert value.prec()>POLE_DEGREE_BOUND
            total += value.add_bigoh(POLE_DEGREE_BOUND+1)
            used += 1
    first=next(([n,str(total[n])] for n in range(-44,POLE_DEGREE_BOUND+1)
                if total[n]!=0),None)
    out={'status':('PASS_EXACT_B_COORDINATE_IDENTITY' if first is None else
                   'FAIL_EXACT_B_COORDINATE_IDENTITY'),
         'source_precision':SOURCE_PRECISION,
         'minimum_input_power_precision':minimum_precision,
         'checked_q_exponents':[-44,POLE_DEGREE_BOUND],
         'pole_degree_bound':POLE_DEGREE_BOUND,
         'integer_denominator':str(denominator),'nonzero_terms':used,
         'first_nonzero_coefficient':first,
         'reconstruction_sha256':sha256(reconstruction_path.read_bytes()).hexdigest()}
    (HERE/'exact_verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True),flush=True)
    assert first is None


if __name__=='__main__':main()
