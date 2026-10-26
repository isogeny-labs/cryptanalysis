"""Search for a cyclic 432-subgroup with generator first rational over F883^3."""
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, set_random_seed

HERE=Path(__file__).resolve().parent


def valuation(n,p):
    v=0
    while n%p==0:
        n//=p;v+=1
    return v


def main():
    protocol=json.loads((HERE/'extension3_protocol.json').read_text())
    census=json.loads((HERE/'class_census.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_CUBIC_GENERATOR_SEARCH'
    p,t=883,20
    t2=t*t-2*p
    t3=t*t2-p*t
    count=p**3+1-t3
    cofactor=count//(2**valuation(count,2)*3**valuation(count,3))
    assert count==688510368 and cofactor==7**2*13*139
    K=GF(p**3,'u')
    set_random_seed(protocol['seed'])
    attempts=classes=0
    found=None
    for row in census['classes']:
        classes+=1
        E=EllipticCurve(K,row['curve_ainvs'])
        for trial in range(protocol['max_random_points_per_curve']):
            attempts+=1
            R=cofactor*E.random_point()
            order=int(R.order())
            v2,v3=valuation(order,2),valuation(order,3)
            if v2<4 or v3<3:
                continue
            P=(2**(v2-4)*3**(v3-3))*R
            if P.order()!=432:
                continue
            frob=E(P[0]**p,P[1]**p)
            for a in protocol['frobenius_eigenvalues_tested']:
                if frob!=a*P:
                    continue
                assert frob!=P and frob!=-P
                found={'curve_j':row['j'],'curve_ainvs':row['curve_ainvs'],
                       'generator':[str(P[0]),str(P[1])],
                       'frobenius_eigenvalue_mod_432':a,'trial_on_curve':trial+1}
                break
            if found:
                break
        if found:
            break
        print(f'checked j={row["j"]} attempts={attempts}',flush=True)
    out={'status':'FOUND' if found else 'BOUNDED_NO_MATCH','prime':p,
         'field_degree':3,'classes_tested':classes,'random_points_tested':attempts,
         'curve_order_extension':count,'witness':found}
    (HERE/'extension3_search.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':
    main()
