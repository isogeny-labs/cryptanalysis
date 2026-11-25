"""Assemble exact certificates for the nonsquare-three source-fiber theorem."""
import json
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

import sympy as sp

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
X,Y=sp.symbols('x y')


def expression(terms):
    return sum(sp.Rational(t['coefficient'])*X**t['x_power']*Y**t['y_power'] for t in terms)


def polynomial(coeffs):
    return sp.Poly.from_list(list(reversed([int(c) for c in coeffs])),X,domain=sp.ZZ)


def main():
    coord_path=ROOT/'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json'
    coord=json.loads(coord_path.read_text())['source_j']
    denominators={Fraction(t['coefficient']).denominator for part in ('numerator','denominator') for t in coord[part]}
    assert all(set(sp.factorint(d)) <= {3,5} for d in denominators)
    h=expression(coord['numerator'])+1728*expression(coord['denominator'])
    curve=Y*Y+Y-X**3+7
    resultant=sp.Poly(sp.resultant(h,curve,Y),X,domain=sp.QQ)
    cert_path=HERE/'sqrt3_certificate.json';cert=json.loads(cert_path.read_text())
    f=polynomial(cert['field_polynomial_coefficients_low_to_high'])
    assert resultant*3**30*5**2==sp.Poly(f*f,X,domain=sp.QQ)
    P=polynomial(cert['sqrt3_numerator_coefficients_low_to_high'])
    H=polynomial(cert['quotient_coefficients_low_to_high'])
    D=int(cert['denominator'])
    assert P*P-sp.Poly(3*D*D,X,domain=sp.ZZ)==f*H
    factors={int(p):int(e) for p,e in sp.factorint(D).items()}
    assert all(sp.isprime(p) for p in factors)
    exceptions=sorted(p for p in factors if p>5 and p%12 in (5,7))
    assert exceptions==[199,5023,19441459]
    exception_path=HERE/'exceptional_result.json';exc=json.loads(exception_path.read_text())
    exception_audit_path=HERE/'exceptional_audit.json';exception_audit=json.loads(exception_audit_path.read_text())
    assert exception_audit['status']=='PASS_INDEPENDENT_EXCEPTIONAL_AUDIT'
    assert exception_audit['exceptional_result_sha256']==sha256(exception_path.read_bytes()).hexdigest()
    assert [c['prime'] for c in exc['cells']]==exceptions
    for cell in exc['cells']:
        p=cell['prime'];assert cell['eliminant_x_roots']==1 and len(cell['x_root_details'])==1
        stored=cell['x_root_details'][0];x=stored['x_C']
        assert f.eval(x)%p==0
        disc=(4*(pow(x,3,p)-7)+1)%p
        assert disc==stored['curve_discriminant'] and pow(disc,(p-1)//2,p)==p-1
    out={'status':'PASS_NONSQUARE_THREE_SOURCE_OBSTRUCTION_CERTIFICATE',
         'scope':'all primes p>5 with 3 nonsquare modulo p and rational source-j map defined',
         'resultant_identity':'Res_y(n+1728d, y^2+y-x^3+7) = f(x)^2/(3^30*5^2)',
         'sqrt3_identity':'P(x)^2-3D^2=f(x)H(x)',
         'exceptional_primes':exceptions,
         'inputs':{str(q.relative_to(ROOT)):sha256(q.read_bytes()).hexdigest()
                   for q in (coord_path,cert_path,exception_path,exception_audit_path)}}
    (HERE/'theorem_receipt.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
