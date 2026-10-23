"""Compute the exact rational j-limit at the noncusp x=16 branch."""
import json
from hashlib import sha256
from pathlib import Path
import sys

from sage.all import PolynomialRing, QQ

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'tools'))
import hecke11 as H

def main():
    _,jfun=H.build([2,3])
    coeffs,x0,_=jfun
    R=PolynomialRing(QQ,'t');t=R.gen();x=QQ(x0)+t
    y=R(QQ(60));g=x**3-x**2-10*x-20
    for k in range(1,12):
        y+=-(y*y+y-g)[k]/QQ(121)*t**k
    assert all((y*y+y-g)[k]==0 for k in range(12))
    num=sum(QQ(v)*x**a*y**b for (a,b),v in coeffs.items())
    low=[num[k] for k in range(11)]
    assert all(c==0 for c in low)
    limit=QQ(num[11])
    assert limit.denominator()==1
    result={'status':'EXACT_REGULAR_J_AT_X16_Y60',
            'regular_j':str(limit),'mod_12763':int(limit)%12763,
            'numerator_zero_coefficients':len(low),
            'source_j_function_sha256':sha256((P/'tools/hecke11.py').read_bytes()).hexdigest(),
            'script_sha256':sha256((P/'exact_regular_j.py').read_bytes()).hexdigest()}
    (P/'exact_regular_j.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
