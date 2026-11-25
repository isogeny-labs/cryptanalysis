"""Complete prime-by-prime accounting for the p<20000, p=11 mod24 gate."""
import json
from fractions import Fraction
from hashlib import sha256
from math import lcm
from pathlib import Path

from sympy import primerange

HERE=Path(__file__).resolve().parent


def rationals(value):
    if isinstance(value,list):
        for child in value:yield from rationals(child)
    else:
        yield Fraction(value)


def main():
    pp=HERE/'bridge_protocol.json';protocol=json.loads(pp.read_text())
    gp=HERE/'bridge_gate.json';gate=json.loads(gp.read_text())
    np=HERE/'norm_audit.json';norm_audit=json.loads(np.read_text())
    bp=HERE/'bad_prime_audit.json';bad_audit=json.loads(bp.read_text())
    rp=HERE/'branch_result.json';branch=json.loads(rp.read_text())
    assert gate['status']=='EXACT_FULL_REDUCTION_BRIDGE_GATE'
    assert norm_audit['status']=='PASS_INDEPENDENT_DETERMINANT_NORM_AUDIT'
    assert norm_audit['bridge_gate_sha256']==sha256(gp.read_bytes()).hexdigest()
    assert branch['bad_prime_audit_sha256']==sha256(bp.read_bytes()).hexdigest()
    base=json.loads(Path(protocol['inputs']['base_certificate']['path']).read_text())
    relative=json.loads(Path(protocol['inputs']['sqrt2_certificate']['path']).read_text())
    coefficient_lists=[base['source_y_numerator_coefficients_low_to_high'],
                       base['source_y_denominator_coefficients_low_to_high'],base['unit']]
    for factor in base['factors']:coefficient_lists.append(factor['coefficients_low_to_high'])
    for record in relative['records']:
        coefficient_lists.append(record['unit'])
        for factor in record['factors']:coefficient_lists.append(factor['coefficients_low_to_high'])
    D=lcm(*(q.denominator for item in coefficient_lists for q in rationals(item)))
    assert D==int(gate['coefficient_denominator_lcm'])
    primes=[int(p) for p in primerange(7,protocol['prime_cap_exclusive']) if p%24==11]
    expected=[]
    for p in primes:
        reasons=[]
        if D%p==0:reasons.append('coefficient_denominator')
        for rec in gate['norms']:
            if int(rec['numerator'])%p==0:reasons.append(rec['name']+'_numerator')
            if int(rec['denominator'])%p==0:reasons.append(rec['name']+'_denominator')
        if reasons:expected.append({'prime':p,'class_mod_24':11,'reasons':reasons})
    saved=[c for c in gate['bad_primes_below_cap'] if c['class_mod_24']==11]
    assert expected==saved
    assert [c['prime'] for c in saved]==[11,131,179,227,251,419,491,1523]
    assert [c['prime'] for c in bad_audit['cells']]==[c['prime'] for c in saved]
    assert [c['prime'] for c in branch['cells']]==[c['prime'] for c in saved]
    exceptions=[]
    for direct,classified in zip(bad_audit['cells'],branch['cells']):
        assert direct['prime']==classified['prime']
        assert direct['rational_CE_pairs']==classified['rational_CE_pairs']
        exceptions.append({'prime':direct['prime'],'C_points':direct['C_points'],
                           'rational_CE_pairs':direct['rational_CE_pairs'],
                           'valid_CEB_triples':classified['status_mix'].get('VALID',0),
                           'status_mix':classified['status_mix']})
    out={'status':'PASS_BOUNDED_11_MOD_24_GATE_ACCOUNTING',
         'scope':'all primes 7<=p<20000 congruent 11 mod 24',
         'prime_cells':len(primes),'norm_certified_good_cells':len(primes)-len(saved),
         'direct_exception_cells':exceptions,
         'rational_CE_positive_primes':[c['prime'] for c in exceptions if c['rational_CE_pairs']],
         'valid_CEB_positive_primes':[c['prime'] for c in exceptions if c['valid_CEB_triples']],
         'inputs':{str(p.name):sha256(p.read_bytes()).hexdigest() for p in (pp,gp,np,bp,rp)}}
    (HERE/'bounded_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('direct_exception_cells','inputs')},sort_keys=True))


if __name__=='__main__':main()
