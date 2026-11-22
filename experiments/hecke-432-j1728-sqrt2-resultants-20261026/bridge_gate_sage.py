"""Complete sufficient good-reduction screen for the sqrt2 factor bridge."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import QQ, ZZ, NumberField, PolynomialRing, lcm, prime_range

HERE=Path(__file__).resolve().parent


def k_eval(v,a,K):
    value=K(0)
    for raw in reversed(v):value=value*a+K(QQ(raw))
    return value


def l_components(v,a,K):
    coeffs=[k_eval(k,a,K) for k in v]
    return coeffs[0],(coeffs[1] if len(coeffs)>1 else K(0))


def rationals_in(value):
    if isinstance(value,list):
        for child in value:yield from rationals_in(child)
    else:
        yield QQ(value)


def main():
    pp=HERE/'bridge_protocol.json';protocol=json.loads(pp.read_text())
    assert protocol['status']=='FROZEN_BEFORE_FULL_REDUCTION_BRIDGE_GATE'
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    base=json.loads(Path(protocol['inputs']['base_certificate']['path']).read_text())
    relative=json.loads(Path(protocol['inputs']['sqrt2_certificate']['path']).read_text())
    pair_norms=json.loads(Path(protocol['inputs']['pair_norms']['path']).read_text())
    assert pair_norms['status']=='EXACT_CONJUGATE_RESULTANT_NORMS'
    Qx=PolynomialRing(QQ,'x')
    K=NumberField(Qx([QQ(c) for c in base['field_polynomial_coefficients_low_to_high']]),'a');a=K.gen()
    all_lists=[base['source_y_numerator_coefficients_low_to_high'],
               base['source_y_denominator_coefficients_low_to_high'],base['unit']]
    for factor in base['factors']:all_lists.append(factor['coefficients_low_to_high'])
    for record in relative['records']:
        all_lists.append(record['unit'])
        for factor in record['factors']:all_lists.append(factor['coefficients_low_to_high'])
    coefficient_denominator=ZZ(lcm([q.denominator() for item in all_lists for q in rationals_in(item)]))
    elements={'source_y_denominator':k_eval(base['source_y_denominator_coefficients_low_to_high'],a,K),
              'base_unit':k_eval(base['unit'],a,K)}
    for record in relative['records']:
        c0,c1=l_components(record['unit'],a,K)
        elements['relative_unit_'+str(record['base_degree'])]=c0*c0-2*c1*c1
    norms=[]
    for name,element in elements.items():
        assert element
        q=QQ(element.norm());assert q
        norms.append({'name':name,'numerator':str(q.numerator()),'denominator':str(q.denominator())})
        print(json.dumps({'name':name,'numerator_digits':len(str(q.numerator())),
                          'denominator_digits':len(str(q.denominator()))}),flush=True)
    for record in pair_norms['rows']:
        norms.append({'name':'pair_resultant_'+str(record['base_degree']),
                      'numerator':record['norm_numerator'],'denominator':record['norm_denominator']})
    bad=[]
    for p in prime_range(7,protocol['prime_cap_exclusive']):
        p=int(p);reasons=[]
        if coefficient_denominator%p==0:reasons.append('coefficient_denominator')
        for rec in norms:
            if int(rec['numerator'])%p==0:reasons.append(rec['name']+'_numerator')
            if int(rec['denominator'])%p==0:reasons.append(rec['name']+'_denominator')
        if reasons:bad.append({'prime':p,'class_mod_24':p%24,'reasons':reasons})
    out={'status':'EXACT_FULL_REDUCTION_BRIDGE_GATE',
         'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
         'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'coefficient_denominator_lcm':str(coefficient_denominator),
         'norms':norms,'bad_primes_below_cap':bad}
    (HERE/'bridge_gate.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'bad_primes':len(bad),
                      'bad_11_mod_24':[c['prime'] for c in bad if c['class_mod_24']==11]}))


if __name__=='__main__':main()
