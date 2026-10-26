"""Select the B-isogeny branch on every point of a complete C fiber."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
FIBER=ROOT/'hecke-432-geometric-fiber-20261025'/'evaluation.json'
E_REL=ROOT/'hecke-432-relative-resolvent-20261025'/'relative_resolvent.json'


def vector(value):
    values=[int(x) for x in value.polynomial().list()]
    return values+[0]*(4-len(values))


def main():
    rec_path=HERE/'reconstruction.json'
    rec=json.loads(rec_path.read_text())
    fiber=json.loads(FIBER.read_text())
    erel=json.loads(E_REL.read_text())
    assert rec['status']=='PASS_RATIONAL_B_RECONSTRUCTION_WITH_HOLDOUT'
    assert fiber['status']=='COMPLETE_GEOMETRIC_E_FIBER'
    assert erel['status']=='CERTIFIED_RELATIVE_DEGREE_12_RESOLVENT'
    assert fiber['selected_C_point']==[639,232]
    base=GF(997)
    R=PolynomialRing(base,'X')
    X=R.gen()
    S=PolynomialRing(R,'T')
    T=S.gen()
    PB=S.zero()
    for (a,b,c),(n,d) in zip(rec['terms'],rec['coefficients_num_den']):
        assert d%997
        PB += S(base(n)/base(d)*base(639)**a*base(232)**b)*T**c
    HE=R.zero()
    for row in erel['terms']:
        a,b,c=(row[k] for k in ('x_C_exponent','y_C_exponent','x_E_exponent'))
        HE += base(int(row['integer_coefficient']))*base(639)**a*base(232)**b*X**c
    resultant=PB.resultant(T**3-X*T**2-64)
    assert PB.degree()==12 and HE.degree()==12 and resultant.degree()==12
    resultant_matches=resultant*HE[12]==HE*resultant[12]

    U=PolynomialRing(base,'u')
    u=U.gen()
    modulus=sum(base(v)*u**i for i,v in enumerate(fiber['field_modulus']))
    extension=GF(997**4,'u',modulus=modulus)
    gen=extension.gen()
    Q=PolynomialRing(extension,'T')
    t=Q.gen()
    pb=Q([extension(PB[i][0]) for i in range(13)])
    rows=[]
    for row in fiber['rows']:
        ex,ey=[sum((extension(v)*gen**i for i,v in enumerate(values)),extension.zero())
               for values in row['E_point']]
        assert ey**2==ex**3+432
        gcd=pb.gcd(t**3-ex*t**2-64)
        assert gcd.degree()==1,(row['index'],gcd.degree())
        xb=-gcd[0]/gcd[1]
        assert xb and xb**3+128
        yb=ey*xb**3/(xb**3+128)
        assert yb**2==xb**3-16
        assert ex==(xb**3-64)/xb**2
        assert ey==yb*(xb**3+128)/xb**3
        rows.append({'index':row['index'],'B_point':[vector(xb),vector(yb)]})
    xs=Counter(tuple(r['B_point'][0]) for r in rows)
    assert len(rows)==24 and len(xs)==12 and set(xs.values())=={2}
    status=('PASS_B_BRANCH_ON_COMPLETE_GEOMETRIC_FIBER' if resultant_matches else
            'FAIL_B_BRANCH_ON_COMPLETE_GEOMETRIC_FIBER')
    out={'status':status,'C_point':fiber['selected_C_point'],
         'field_modulus':fiber['field_modulus'],
         'resultant_matches_E_resolvent':resultant_matches,
         'resultant_scale_mod_997':int(resultant[12]/HE[12]),
         'B_points':rows,'distinct_x_B':len(xs),'x_B_multiplicities':dict(Counter(xs.values())),
         'source_sha256':{'reconstruction':sha256(rec_path.read_bytes()).hexdigest(),
                          'E_resolvent':sha256(E_REL.read_bytes()).hexdigest(),
                          'geometric_fiber':sha256(FIBER.read_bytes()).hexdigest()}}
    (HERE/'fiber_verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','resultant_matches_E_resolvent',
             'distinct_x_B','resultant_scale_mod_997')},sort_keys=True))
    assert resultant_matches


if __name__=='__main__':main()
