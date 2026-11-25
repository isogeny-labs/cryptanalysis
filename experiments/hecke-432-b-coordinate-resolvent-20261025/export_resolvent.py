"""Publish the primitive integer x_B resolvent and its evidence links."""
import json
from hashlib import sha256
from math import gcd,lcm
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    reconstruction_path=HERE/'reconstruction.json'
    exact_path=HERE/'exact_verification.json'
    fiber_path=HERE/'fiber_verification.json'
    rec=json.loads(reconstruction_path.read_text())
    exact=json.loads(exact_path.read_text())
    fiber=json.loads(fiber_path.read_text())
    assert rec['status']=='PASS_RATIONAL_B_RECONSTRUCTION_WITH_HOLDOUT'
    assert exact['status']=='PASS_EXACT_B_COORDINATE_IDENTITY'
    assert fiber['status']=='PASS_B_BRANCH_ON_COMPLETE_GEOMETRIC_FIBER'
    denominator=lcm(*(d for _,d in rec['coefficients_num_den']))
    terms=[{'x_C_exponent':a,'y_C_exponent':b,'x_B_exponent':c,
            'integer_coefficient':str(n*(denominator//d))}
           for (a,b,c),(n,d) in zip(rec['terms'],rec['coefficients_num_den']) if n]
    assert len(terms)==89
    assert gcd(*(int(row['integer_coefficient']) for row in terms))==1
    assert max(row['x_B_exponent'] for row in terms)==12
    out={'status':'CERTIFIED_RELATIVE_DEGREE_12_B_RESOLVENT',
         'base_curve':'C: y_C^2+y_C=x_C^3-7 = X_0(27)',
         'target_curve':'B: y_B^2=x_B^3-16 = 432a1',
         'polynomial':'sum(integer_coefficient*x_C^a*y_C^b*X^c)',
         'degree_in_X':12,'weighted_degree':44,'pole_degree_bound':1056,
         'integer_coefficient_gcd':1,'coefficient_of_xC4_yC0_X0':str(denominator),
         'terms':terms,
         'source_sha256':{'reconstruction':sha256(reconstruction_path.read_bytes()).hexdigest(),
                          'exact_verification':sha256(exact_path.read_bytes()).hexdigest(),
                          'fiber_verification':sha256(fiber_path.read_bytes()).hexdigest()}}
    (HERE/'relative_b_resolvent.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'terms':len(terms),
                      'integer_denominator':denominator},sort_keys=True))


if __name__=='__main__':main()
