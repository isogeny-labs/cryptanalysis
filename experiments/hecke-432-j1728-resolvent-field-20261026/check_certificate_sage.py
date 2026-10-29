"""Replay the exact factor certificate and its finite-field reductions."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from sage.all import QQ, ZZ, GF, NumberField, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def eval_q_vector(coeffs,x,F):
    value=F(0)
    for c in reversed(coeffs):
        q=QQ(c)
        value=value*x+F(q.numerator())/F(q.denominator())
    return value


def to_K(coeffs,a,K):
    value=K(0)
    for c in reversed(coeffs):value=value*a+K(QQ(c))
    return value


def main():
    pp=HERE/'protocol.json';protocol=json.loads(pp.read_text())
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    cp=HERE/'factor_certificate.json';cert=json.loads(cp.read_text())
    result=json.loads((HERE/'field_factor_result.json').read_text())
    assert sha256(cp.read_bytes()).hexdigest()==result['factor_certificate_sha256']
    Qx=PolynomialRing(QQ,'x');f=Qx([QQ(v) for v in cert['field_polynomial_coefficients_low_to_high']])
    assert f.degree()==18 and f.is_irreducible()
    K=NumberField(f,'a');a=K.gen()
    numerator=to_K(cert['source_y_numerator_coefficients_low_to_high'],a,K)
    denominator=to_K(cert['source_y_denominator_coefficients_low_to_high'],a,K)
    assert denominator
    y=numerator/denominator
    assert y*y+y==a**3-7
    Kz=PolynomialRing(K,'z');z=Kz.gen()
    unit=to_K(cert['unit'],a,K)
    factors=[(Kz([to_K(c,a,K) for c in record['coefficients_low_to_high']]),record['multiplicity'])
             for record in cert['factors']]
    assert [int(g.degree()) for g,m in factors]==[4,8]
    product=Kz(unit)
    for g,m in factors:
        assert g.is_irreducible()
        product*=g**m
    resolvent=json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())['terms']
    direct=Kz.zero()
    for t in resolvent:
        direct+=ZZ(t['integer_coefficient'])*a**t['x_C_exponent']*y**t['y_C_exponent']*z**t['x_E_exponent']
    assert product==direct
    prior=ROOT/'experiments/hecke-432-j1728-ce-factor-20261026/refined_test_result.json'
    tested=json.loads(prior.read_text());reductions=[]
    for row in tested['rows']:
        p=row['prime'];F=GF(p);R=PolynomialRing(F,'z');zz=R.gen()
        x,y0=map(F,row['C_point'])
        ny=eval_q_vector(cert['source_y_numerator_coefficients_low_to_high'],x,F)
        dy=eval_q_vector(cert['source_y_denominator_coefficients_low_to_high'],x,F)
        assert dy and ny/dy==y0
        specialized_unit=eval_q_vector(cert['unit'],x,F)
        specialized_factors=[];degree_parts=[]
        for record in cert['factors']:
            g=R([eval_q_vector(c,x,F) for c in record['coefficients_low_to_high']])
            specialized_factors.append((g,record['multiplicity']))
            degree_parts.append(sorted([int(h.degree()) for h,m in g.factor() for _ in range(m)]))
        prod=R(specialized_unit)
        for g,m in specialized_factors:prod*=g**m
        direct_mod=R.zero()
        for t in resolvent:
            direct_mod+=F(int(t['integer_coefficient']))*x**t['x_C_exponent']*y0**t['y_C_exponent']*zz**t['x_E_exponent']
        assert prod==direct_mod
        assert sorted(degree_parts[0]+degree_parts[1])==row['factor_degrees']
        reductions.append({'prime':p,'C_point':row['C_point'],'quartic_degrees':degree_parts[0],
                           'octic_degrees':degree_parts[1]})
    out={'status':'PASS_EXACT_CERTIFICATE_AND_REDUCTIONS',
         'factor_certificate_sha256':sha256(cp.read_bytes()).hexdigest(),
         'refined_test_sha256':sha256(prior.read_bytes()).hexdigest(),
         'exact_irreducible_degrees':[4,8],
         'reduction_rows':len(reductions),
         'pattern_counts':{str(k):v for k,v in Counter((tuple(r['quartic_degrees']),tuple(r['octic_degrees'])) for r in reductions).items()},
         'reductions':reductions}
    (HERE/'certificate_check.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='reductions'},sort_keys=True))


if __name__=='__main__':main()
