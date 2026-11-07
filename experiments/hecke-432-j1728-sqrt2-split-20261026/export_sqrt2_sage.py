"""Export the exact sqrt(2)-conjugate factor pairs of the C-E resolvent."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import QQ, NumberField, PolynomialRing

HERE=Path(__file__).resolve().parent


def from_k_vector(coeffs,a,K):
    value=K(0)
    for c in reversed(coeffs):value=value*a+K(QQ(c))
    return value


def k_vector(c):
    return [str(q) for q in c.polynomial().list()]


def l_vector(c):
    return [k_vector(q) for q in c.list()]


def main():
    pp=HERE/'protocol.json';protocol=json.loads(pp.read_text())
    assert protocol['status']=='FROZEN_BEFORE_SQRT2_CONJUGATE_CERTIFICATE'
    cp=Path(protocol['input']['path'])
    assert sha256(cp.read_bytes()).hexdigest()==protocol['input']['sha256']
    cert=json.loads(cp.read_text())
    Qx=PolynomialRing(QQ,'x')
    f=Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']])
    K=NumberField(f,'a');a=K.gen()
    assert not K(2).is_square()
    Kt=PolynomialRing(K,'t');t=Kt.gen()
    L=K.extension(t*t-2,'s');s=L.gen()
    Lz=PolynomialRing(L,'z')

    def conjugate(c):
        v=c.list()
        return L(v[0])-(L(v[1])*s if len(v)>1 else L(0))

    records=[];summaries=[]
    for base in cert['factors']:
        g=Lz([L(from_k_vector(c,a,K)) for c in base['coefficients_low_to_high']])
        factorization=g.factor()
        assert factorization.prod()==g
        pieces=[(q,int(m)) for q,m in factorization]
        assert len(pieces)==2 and all(m==1 for q,m in pieces)
        assert all(q.is_irreducible() for q,m in pieces)
        q0,q1=(pieces[0][0],pieces[1][0])
        sigma_q0=Lz([conjugate(c) for c in q0.list()]).monic()
        sigma_q1=Lz([conjugate(c) for c in q1.list()]).monic()
        print(json.dumps({'stage':'conjugacy_probe','base_degree':int(g.degree()),
                          'degrees':[int(q0.degree()),int(q1.degree())],
                          'sigma_0_to_0':bool(sigma_q0==q0.monic()),
                          'sigma_0_to_1':bool(sigma_q0==q1.monic()),
                          'sigma_1_to_0':bool(sigma_q1==q0.monic())}),flush=True)
        assert sigma_q0==q1.monic()
        assert sigma_q1==q0.monic()
        assert q0.gcd(q1).degree()==0
        assert q0.resultant(q1)!=0
        records.append({'base_degree':int(g.degree()),'unit':l_vector(factorization.unit()),
                        'factors':[{'degree':int(q.degree()),
                                    'coefficients_low_to_high':[l_vector(c) for c in q.list()]}
                                   for q in (q0,q1)]})
        summaries.append({'base_degree':int(g.degree()),
                          'extension_degrees':sorted([int(q0.degree()),int(q1.degree())]),
                          'conjugate_pair':True,'coprime':True})
        print(json.dumps(summaries[-1],sort_keys=True),flush=True)
    out={'status':'EXACT_SQRT2_CONJUGATE_FACTOR_CERTIFICATE',
         'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
         'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'source_certificate_sha256':sha256(cp.read_bytes()).hexdigest(),
         'field_polynomial_coefficients_low_to_high':cert['field_polynomial_coefficients_low_to_high'],
         'extension_polynomial':'s^2-2','records':records,'summaries':summaries}
    path=HERE/'sqrt2_factor_certificate.json'
    path.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'certificate_bytes':path.stat().st_size}))


if __name__=='__main__':main()
