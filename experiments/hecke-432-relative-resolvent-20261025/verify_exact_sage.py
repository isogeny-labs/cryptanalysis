"""Exact Q-series certificate for the relative resolvent via pole degree."""
import json
from hashlib import sha256
from math import lcm
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, Infinity, QQ

HERE = Path(__file__).resolve().parent
SOURCE_PRECISION = 3500
POLE_DEGREE_BOUND = 3312


def main():
    reconstruction_path = HERE/'reconstruction.json'
    rec = json.loads(reconstruction_path.read_text())
    assert rec['status'] == 'PASS_RATIONAL_RECONSTRUCTION_WITH_FRESH_PRIME_HOLDOUT'
    terms = rec['terms']
    ratios = rec['coefficients_num_den']
    denominator = lcm(*(d for _,d in ratios))
    integer_coefficients = [n*(denominator//d) for n,d in ratios]
    assert integer_coefficients[0] == denominator
    assert max(2*a+3*b+2*c for a,b,c in terms) == 90
    # C is reached by a degree-24 forgetful map. E is reached through the
    # degree-24 optimal B map followed by a degree-three isogeny. Thus the
    # three coordinate functions have degrees 48, 72, and 144 here.
    assert max(48*a+72*b+144*c for a,b,c in terms) == POLE_DEGREE_BOUND

    C = EllipticCurve('27a1')
    B = EllipticCurve(QQ,[0,0,0,0,-16])
    xc,yc = C.modular_parametrization().power_series(SOURCE_PRECISION)
    xb,_ = B.modular_parametrization().power_series(SOURCE_PRECISION)
    xe = (xb**3-64)/xb**2
    ring = xc.parent()
    xcp = [xc**a for a in range(46)]
    xep = [xe**c for c in range(13)]
    minimum_precision = min(int(s.prec()) for s in xcp+xep+[yc]
                            if s.prec() != Infinity)
    assert minimum_precision > POLE_DEGREE_BOUND
    total = ring.zero()
    used = 0
    for (a,b,c), coefficient in zip(terms,integer_coefficients):
        if coefficient:
            value = coefficient*xcp[a]*(yc if b else ring.one())*xep[c]
            assert value.prec() > POLE_DEGREE_BOUND
            total += value.add_bigoh(POLE_DEGREE_BOUND+1)
            used += 1
    zero = all(total[n] == 0 for n in range(-90,POLE_DEGREE_BOUND+1))
    out = {'status':('PASS_EXACT_RELATIVE_RESOLVENT_IDENTITY' if zero else
                     'FAIL_EXACT_RELATIVE_RESOLVENT_IDENTITY'),
           'source_precision':SOURCE_PRECISION,
           'minimum_input_power_precision':minimum_precision,
           'checked_q_exponents':[-90,POLE_DEGREE_BOUND],
           'pole_degree_bound':POLE_DEGREE_BOUND,
           'integer_denominator':str(denominator),
           'nonzero_terms':used,
           'reconstruction_sha256':sha256(reconstruction_path.read_bytes()).hexdigest(),
           'first_nonzero_coefficient':next(([n,str(total[n])] for n in range(-90,POLE_DEGREE_BOUND+1)
                                            if total[n] != 0),None)}
    (HERE/'exact_verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True),flush=True)
    assert zero


if __name__ == '__main__':
    main()
