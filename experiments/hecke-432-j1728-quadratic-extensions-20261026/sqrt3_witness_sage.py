"""Export an integer polynomial certificate that the source field contains sqrt(3)."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import QQ, ZZ, NumberField, PolynomialRing, lcm

HERE=Path(__file__).resolve().parent


def main():
    pp=HERE/'protocol.json';protocol=json.loads(pp.read_text())
    cp=Path(protocol['input']['path'])
    assert sha256(cp.read_bytes()).hexdigest()==protocol['input']['sha256']
    cert=json.loads(cp.read_text())
    Zx=PolynomialRing(ZZ,'x');f=Zx([ZZ(c) for c in cert['field_polynomial_coefficients_low_to_high']])
    Qx=PolynomialRing(QQ,'x');K=NumberField(Qx(f),'a');a=K.gen()
    root=K(3).sqrt()
    assert root*root==3
    coeffs=root.polynomial().list()
    D=ZZ(lcm([q.denominator() for q in coeffs]))
    P=Zx([ZZ(D*q) for q in coeffs])
    H,remainder=(P*P-3*D*D).quo_rem(f)
    assert remainder==0 and P.degree()<f.degree()
    assert P(a)*P(a)==3*D*D
    out={'status':'EXACT_SQRT3_POLYNOMIAL_IDENTITY',
         'source_certificate_sha256':sha256(cp.read_bytes()).hexdigest(),
         'field_polynomial_coefficients_low_to_high':[str(c) for c in f.list()],
         'denominator':str(D),
         'sqrt3_numerator_coefficients_low_to_high':[str(c) for c in P.list()],
         'quotient_coefficients_low_to_high':[str(c) for c in H.list()],
         'identity':'P(x)^2 - 3 D^2 = f(x) H(x) over Z[x]'}
    (HERE/'sqrt3_certificate.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'denominator_digits':len(str(D)),
                      'P_degree':int(P.degree()),'H_degree':int(H.degree())}))


if __name__=='__main__':main()
