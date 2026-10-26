"""Check the explicit N/D branch on the full F_997^4 geometric fiber."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE='/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF,PolynomialRing

HERE=Path(__file__).resolve().parent
FIBER=HERE.parent/'hecke-432-geometric-fiber-20261025'/'evaluation.json'


def main():
    branch_path=HERE/'branch_formula.json'
    points_path=HERE/'fiber_verification.json'
    branch=json.loads(branch_path.read_text())
    points=json.loads(points_path.read_text())
    fiber=json.loads(FIBER.read_text())
    assert branch['status']=='EXPLICIT_RATIONAL_B_X_BRANCH'
    assert points['status']=='PASS_B_BRANCH_ON_COMPLETE_GEOMETRIC_FIBER'
    base=GF(997)
    U=PolynomialRing(base,'u')
    u=U.gen()
    modulus=sum(base(v)*u**i for i,v in enumerate(fiber['field_modulus']))
    extension=GF(997**4,'u',modulus=modulus)
    gen=extension.gen()
    def element(values):
        return sum((extension(v)*gen**i for i,v in enumerate(values)),extension.zero())
    def evaluate(terms,xc,yc,xe):
        return sum((extension(int(row['integer_coefficient']))*
                    xc**row['x_C_exponent']*yc**row['y_C_exponent']*
                    xe**row['x_E_exponent'] for row in terms),extension.zero())
    xc,yc=map(extension,fiber['selected_C_point'])
    checked=[]
    for source,selected in zip(fiber['rows'],points['B_points']):
        assert source['index']==selected['index']
        xe,ye=map(element,source['E_point'])
        xb,yb=map(element,selected['B_point'])
        n=evaluate(branch['numerator_terms'],xc,yc,xe)
        d=evaluate(branch['denominator_terms'],xc,yc,xe)
        assert d!=0 and n/d==xb
        assert yb==ye*xb**3/(xb**3+128)
        checked.append(source['index'])
    out={'status':'PASS_EXPLICIT_B_BRANCH_ON_COMPLETE_FIBER',
         'source_points':len(fiber['rows']),'nonzero_denominators':len(checked),
         'matching_B_points':len(checked),'indices':checked,
         'source_sha256':{'formula':sha256(branch_path.read_bytes()).hexdigest(),
                          'B_fiber':sha256(points_path.read_bytes()).hexdigest(),
                          'geometric_fiber':sha256(FIBER.read_bytes()).hexdigest()}}
    (HERE/'branch_fiber_verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','source_points',
                 'nonzero_denominators','matching_B_points')},sort_keys=True))


if __name__=='__main__':main()
