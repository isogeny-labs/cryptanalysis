"""Independent exact and finite-field replay of the sqrt2 factor certificate."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from sage.all import QQ, GF, NumberField, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def q_eval(v,x,F):
    value=F(0)
    for raw in reversed(v):
        c=QQ(raw)
        value=value*x+F(c.numerator())/F(c.denominator())
    return value


def k_eval(v,a,K):
    value=K(0)
    for raw in reversed(v):value=value*a+K(QQ(raw))
    return value


def l_eval(v,a,s,K,L):
    return sum((L(k_eval(k,a,K))*s**i for i,k in enumerate(v)),L(0))


def finite_eval(v,x,s,E):
    return sum((q_eval(k,x,E)*s**i for i,k in enumerate(v)),E(0))


def main():
    pp=HERE/'protocol.json';protocol=json.loads(pp.read_text())
    cert_path=HERE/'sqrt2_factor_certificate.json';cert=json.loads(cert_path.read_text())
    assert cert['status']=='EXACT_SQRT2_CONJUGATE_FACTOR_CERTIFICATE'
    assert cert['protocol_sha256']==sha256(pp.read_bytes()).hexdigest()
    base_path=Path(protocol['input']['path']);base=json.loads(base_path.read_text())
    assert cert['source_certificate_sha256']==sha256(base_path.read_bytes()).hexdigest()
    Qx=PolynomialRing(QQ,'x')
    K=NumberField(Qx([QQ(c) for c in base['field_polynomial_coefficients_low_to_high']]),'a');a=K.gen()
    Kt=PolynomialRing(K,'t');t=Kt.gen()
    L=K.extension(t*t-2,'s');s=L.gen()
    Lz=PolynomialRing(L,'z')

    def conjugate(c):
        v=c.list()
        return L(v[0])-(L(v[1])*s if len(v)>1 else L(0))

    reconstructed=[]
    for original,record in zip(base['factors'],cert['records']):
        target=Lz([L(k_eval(v,a,K)) for v in original['coefficients_low_to_high']])
        unit=l_eval(record['unit'],a,s,K,L)
        g0,g1=[Lz([l_eval(c,a,s,K,L) for c in factor['coefficients_low_to_high']])
               for factor in record['factors']]
        assert unit*g0*g1==target
        assert g0.is_irreducible() and g1.is_irreducible()
        assert g0.gcd(g1).degree()==0
        assert Lz([conjugate(c) for c in g0.list()]).monic()==g1.monic()
        assert Lz([conjugate(c) for c in g1.list()]).monic()==g0.monic()
        reconstructed.append((unit,g0,g1))
    print(json.dumps({'stage':'exact_replay','factor_degrees':[[int(g0.degree()),int(g1.degree())] for _,g0,g1 in reconstructed]}),flush=True)

    prior_path=ROOT/'experiments/hecke-432-j1728-ce-factor-20261026/refined_test_result.json'
    prior=json.loads(prior_path.read_text())
    rows=[]
    for original in prior['rows']:
        if original['class_mod_24'] not in (11,23):continue
        p=original['prime'];x=original['C_point'][0]
        F=GF(p)
        nonsquare_two=not F(2).is_square()
        assert nonsquare_two==(p%24==11)
        E=GF(p*p,'u') if nonsquare_two else F
        s0=E(2).sqrt()
        Ez=PolynomialRing(E,'z')
        parts=[]
        for original_factor,record in zip(base['factors'],cert['records']):
            unit=finite_eval(record['unit'],E(x),s0,E)
            pair=[Ez([finite_eval(c,E(x),s0,E) for c in item['coefficients_low_to_high']])
                  for item in record['factors']]
            original_mod=Ez([q_eval(v,E(x),E) for v in original_factor['coefficients_low_to_high']])
            assert unit*pair[0]*pair[1]==original_mod
            assert pair[0].gcd(pair[1]).degree()==0
            if nonsquare_two:
                assert s0**p==-s0
                assert Ez([c**p for c in pair[0].list()]).monic()==pair[1].monic()
                assert Ez([c**p for c in pair[1].list()]).monic()==pair[0].monic()
                Fz=PolynomialRing(F,'z')
                original_over_F=Fz([q_eval(v,F(x),F) for v in original_factor['coefficients_low_to_high']])
                assert not original_over_F.roots(multiplicities=False)
            parts.append([len(q.roots(multiplicities=False)) for q in pair])
        if not nonsquare_two:
            assert sum(sum(pair) for pair in parts)==4
        rows.append({'prime':p,'C_point':original['C_point'],
                     'two_nonsquare':nonsquare_two,
                     'pair_root_counts':parts,
                     'coprime_mod_p':True})
    out={'status':'PASS_EXACT_AND_FINITE_SQRT2_CONJUGACY_CHECK',
         'certificate_sha256':sha256(cert_path.read_bytes()).hexdigest(),
         'prior_test_sha256':sha256(prior_path.read_bytes()).hexdigest(),
         'rows':rows,
         'summary':{'rows':len(rows),'nonsquare_two_rows':sum(r['two_nonsquare'] for r in rows),
                    'root_pattern_counts':{str(k):v for k,v in Counter(tuple(tuple(p) for p in r['pair_root_counts']) for r in rows).items()}}}
    (HERE/'certificate_check.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],**out['summary']},sort_keys=True))


if __name__=='__main__':main()
