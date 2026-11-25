"""Exact norms of the sqrt2-conjugate factor-pair resultants."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import QQ, ZZ, NumberField, PolynomialRing, lcm, prime_range

HERE=Path(__file__).resolve().parent


def base_element(v,a,K):
    x=K(0)
    for raw in reversed(v):x=x*a+K(QQ(raw))
    return x


def relative_element(v,a,s,K,L):
    return sum((L(base_element(k,a,K))*s**i for i,k in enumerate(v)),L(0))


def all_rationals(cert):
    for record in cert['records']:
        for k in record['unit']:
            for raw in k:yield QQ(raw)
        for factor in record['factors']:
            for c in factor['coefficients_low_to_high']:
                for k in c:
                    for raw in k:yield QQ(raw)


def main():
    pp=HERE/'protocol.json';protocol=json.loads(pp.read_text())
    assert protocol['status']=='FROZEN_BEFORE_CONJUGATE_RESULTANT_NORMS'
    cp=Path(protocol['input']['path'])
    assert sha256(cp.read_bytes()).hexdigest()==protocol['input']['sha256']
    cert=json.loads(cp.read_text())
    Qx=PolynomialRing(QQ,'x')
    K=NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]),'a');a=K.gen()
    Kt=PolynomialRing(K,'t');t=Kt.gen()
    L=K.extension(t*t-2,'s');s=L.gen()
    Lz=PolynomialRing(L,'z')
    denominator=ZZ(lcm([q.denominator() for q in all_rationals(cert)]))
    rows=[]
    for record in cert['records']:
        pair=[Lz([relative_element(v,a,s,K,L) for v in factor['coefficients_low_to_high']])
              for factor in record['factors']]
        assert len(pair)==2 and pair[0].gcd(pair[1]).degree()==0
        resultant=pair[0].resultant(pair[1])
        assert resultant
        relative_vector=resultant.list()
        assert len(relative_vector)==1 or all(not c for c in relative_vector[1:])
        base_resultant=K(relative_vector[0])
        norm=QQ(base_resultant.norm())
        assert norm
        row={'base_degree':record['base_degree'],
             'pair_degrees':[int(g.degree()) for g in pair],
             'resultant_in_K':True,
             'resultant_coefficients_low_to_high':[str(c) for c in base_resultant.polynomial().list()],
             'norm_numerator':str(norm.numerator()),
             'norm_denominator':str(norm.denominator())}
        rows.append(row)
        print(json.dumps({'base_degree':row['base_degree'],
                          'norm_numerator_digits':len(row['norm_numerator']),
                          'norm_denominator_digits':len(row['norm_denominator'])}),flush=True)
    bad=[]
    for p in prime_range(7,protocol['prime_cap_exclusive']):
        p=int(p);reasons=[]
        if denominator%p==0:reasons.append('coefficient_denominator')
        for row in rows:
            if int(row['norm_numerator'])%p==0:reasons.append('resultant_norm_'+str(row['base_degree']))
            if int(row['norm_denominator'])%p==0:reasons.append('norm_denominator_'+str(row['base_degree']))
        if reasons:bad.append({'prime':p,'class_mod_24':p%24,'reasons':reasons})
    out={'status':'EXACT_CONJUGATE_RESULTANT_NORMS',
         'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
         'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'input_certificate_sha256':sha256(cp.read_bytes()).hexdigest(),
         'coefficient_denominator_lcm':str(denominator),
         'rows':rows,'bad_primes_below_cap':bad}
    (HERE/'resultant_norms.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'bad_primes':len(bad),
                      'bad_11_mod_24':[c['prime'] for c in bad if c['class_mod_24']==11]}))


if __name__=='__main__':main()
