"""Independent integer-polynomial replay of the sqrt(3) witness."""
import json
from hashlib import sha256
from pathlib import Path

from sympy import Poly, Symbol, factorint

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
X=Symbol('x')


def poly(coeffs):
    return Poly.from_list(list(reversed([int(c) for c in coeffs])),X,domain='ZZ')


def main():
    cp=HERE/'sqrt3_certificate.json';c=json.loads(cp.read_text())
    assert c['status']=='EXACT_SQRT3_POLYNOMIAL_IDENTITY'
    f=poly(c['field_polynomial_coefficients_low_to_high'])
    P=poly(c['sqrt3_numerator_coefficients_low_to_high'])
    H=poly(c['quotient_coefficients_low_to_high'])
    D=int(c['denominator'])
    assert P*P-Poly(3*D*D,X,domain='ZZ')==f*H
    factors={int(p):int(e) for p,e in factorint(D).items()}
    assert all(p>1 for p in factors)
    exceptional=sorted(p for p in factors if p>5 and p%12 in (5,7))
    records={}
    for label,path in {
        'class5':ROOT/'experiments/hecke-432-j1728-ordinary-holdout-20261026/sieve_result.json',
        'class7':ROOT/'experiments/hecke-432-j1728-cubic-twist-holdout-20261026/sieve_result.json'
    }.items():
        data=json.loads(path.read_text());ps=[cell['prime'] for cell in data['cells']]
        assert all(D%p for p in ps)
        assert all(pow(3,(p-1)//2,p)==p-1 for p in ps)
        assert all(not cell['j1728_C_points'] for cell in data['cells'])
        records[label]={'cells':len(ps),'screen_sha256':sha256(path.read_bytes()).hexdigest(),
                        'denominator_invertible':True,'three_nonsquare':True,'C_empty':True}
    out={'status':'PASS_INDEPENDENT_SQRT3_IDENTITY_AUDIT',
         'certificate_sha256':sha256(cp.read_bytes()).hexdigest(),
         'denominator_factorization':{str(p):e for p,e in factors.items()},
         'exceptional_nonsquare_primes':exceptional,'screen_replays':records}
    (HERE/'sqrt3_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
