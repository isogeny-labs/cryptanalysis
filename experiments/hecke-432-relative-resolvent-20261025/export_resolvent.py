"""Publish a compact integer-coefficient representation of the resolvent."""
import json
from hashlib import sha256
from math import gcd, lcm
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    reconstruction_path = HERE/'reconstruction.json'
    exact_path = HERE/'exact_verification.json'
    fiber_path = HERE/'fiber_verification.json'
    rec = json.loads(reconstruction_path.read_text())
    exact = json.loads(exact_path.read_text())
    fiber = json.loads(fiber_path.read_text())
    assert rec['status'] == 'PASS_RATIONAL_RECONSTRUCTION_WITH_FRESH_PRIME_HOLDOUT'
    assert exact['status'] == 'PASS_EXACT_RELATIVE_RESOLVENT_IDENTITY'
    assert fiber['status'] == 'PASS_SPECIALIZED_RELATIVE_RESOLVENT_FIBER'
    denominator = lcm(*(d for _,d in rec['coefficients_num_den']))
    terms = [{'x_C_exponent':a,'y_C_exponent':b,'x_E_exponent':c,
              'integer_coefficient':str(n*(denominator//d))}
             for (a,b,c),(n,d) in zip(rec['terms'],rec['coefficients_num_den']) if n]
    coefficient_gcd = gcd(*(int(t['integer_coefficient']) for t in terms))
    assert len(terms) == 278 and coefficient_gcd == 1
    assert max(t['x_E_exponent'] for t in terms) == 12
    assert max(2*t['x_C_exponent']+3*t['y_C_exponent']+2*t['x_E_exponent']
               for t in terms) == 90
    out = {'status':'CERTIFIED_RELATIVE_DEGREE_12_RESOLVENT',
           'base_curve':'C: y_C^2+y_C=x_C^3-7 = X_0(27)',
           'target_curve':'E: y_E^2=x_E^3+432',
           'polynomial':'sum(integer_coefficient*x_C^a*y_C^b*X^c)',
           'integer_coefficient_gcd':coefficient_gcd,
           'coefficient_of_xC0_yC0_X0':str(denominator),
           'degree_in_X':12,'weighted_degree':90,'pole_degree_bound':3312,
           'terms':terms,
           'source_sha256':{
               'reconstruction':sha256(reconstruction_path.read_bytes()).hexdigest(),
               'exact_verification':sha256(exact_path.read_bytes()).hexdigest(),
               'fiber_verification':sha256(fiber_path.read_bytes()).hexdigest()}}
    (HERE/'relative_resolvent.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'nonzero_terms':len(terms),
                      'degree_in_X':out['degree_in_X'],'coefficient_gcd':coefficient_gcd},sort_keys=True))


if __name__ == '__main__':
    main()
