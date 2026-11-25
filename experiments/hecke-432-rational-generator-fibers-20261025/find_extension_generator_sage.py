"""Find one F883-rational cyclic 432-subgroup with generator over F883^2."""
import json
from math import gcd
from pathlib import Path

from sage.all import EllipticCurve, GF, set_random_seed

HERE=Path(__file__).resolve().parent


def point_text(P):
    return [str(P[0]),str(P[1])]


def main():
    protocol=json.loads((HERE/'extension_protocol.json').read_text())
    census=json.loads((HERE/'class_census.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_EXTENSION_GENERATOR_SEARCH'
    p=protocol['prime']
    K=GF(p**2,'u')
    set_random_seed(protocol['seed'])
    eigenvalues=[a for a in range(432) if gcd(a,432)==1 and
                 (a*a-protocol['trace']*a+p)%432==0 and a not in (1,431) and a*a%432==1]
    assert eigenvalues==[217]
    attempts=0
    tested_classes=0
    found=None
    for row in census['classes']:
        if row['curve_order']!=864:
            continue
        tested_classes+=1
        E=EllipticCurve(K,row['curve_ainvs'])
        for trial in range(protocol['max_random_points_per_curve']):
            attempts+=1
            R=113*E.random_point()
            order=int(R.order())
            if order%27 or order%16:
                continue
            v2=0
            n=order
            while n%2==0:
                v2+=1;n//=2
            if v2<4:
                continue
            P=(2**(v2-4))*R
            if P.order()!=432:
                continue
            frob=E(P[0]**p,P[1]**p)
            if frob!=217*P:
                continue
            assert frob!=P and frob!= -P
            found={'curve_j':row['j'],'curve_ainvs':row['curve_ainvs'],
                   'generator':point_text(P),'generator_order':432,
                   'frobenius_eigenvalue_mod_432':217,
                   'frobenius_order_on_generator':2,
                   'trial_on_curve':trial+1}
            break
        if found:
            break
        print(f'checked class j={row["j"]} attempts={attempts}',flush=True)
    out={'status':'FOUND' if found else 'BOUNDED_NO_MATCH',
         'prime':p,'field_degree':2,'classes_tested':tested_classes,
         'random_points_tested':attempts,'eigenvalue_tested':217,
         'witness':found}
    (HERE/'extension_search.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':
    main()
