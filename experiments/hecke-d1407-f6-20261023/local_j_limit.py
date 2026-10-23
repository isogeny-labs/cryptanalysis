"""Evaluate the j-function at both x=16 branches using local x-series."""
import hashlib
import json
from pathlib import Path
import sys

from sage.all import PolynomialRing

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'tools'))
import hecke11 as H

def expansion(rd,y0,degree=11):
    R=PolynomialRing(rd.Fp,'t');t=R.gen();x=rd.Fp(16)+t
    y=R(rd.Fp(y0));g=x**3-x**2-10*x-20
    for k in range(1,degree+1):
        residual=(y*y+y-g)[k]
        a=-residual/(2*rd.Fp(y0)+1)
        y+=a*t**k
    assert all((y*y+y-g)[k]==0 for k in range(degree+1))
    numerator=rd.A(x,y)
    coeffs=[int(numerator[k]) for k in range(degree+1)]
    return {'point':str(rd.E(rd.Fp(16),rd.Fp(y0))),
            'numerator_coefficients_through_11':coeffs,
            'regular_limit_j':coeffs[11] if all(v==0 for v in coeffs[:11]) else None,
            'numerator_valuation_at_least_11':all(v==0 for v in coeffs[:11])}

def main():
    funcs,jfun=H.build([2,3]);rd=H.Reduced(12763,funcs,jfun,[2,3])
    branches=[expansion(rd,60),expansion(rd,-61)]
    result={'status':'LOCAL_J_LIMIT_CERTIFICATE',
            'script_sha256':hashlib.sha256((P/'local_j_limit.py').read_bytes()).hexdigest(),
            'branches':branches}
    (P/'local_j_limit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
