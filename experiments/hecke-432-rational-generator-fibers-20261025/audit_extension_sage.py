"""Independent replay of the cubic witness and field-embedding invariance."""
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, sage_eval

HERE=Path(__file__).resolve().parent


def main():
    witness=json.loads((HERE/'extension3_search.json').read_text())['witness']
    prior=json.loads((HERE/'forward_census.json').read_text())
    rows=[json.loads((HERE/f'extension3_evaluation_{i}.json').read_text()) for i in range(3)]
    p=883
    K=GF(p**3,'u')
    u=K.gen()
    E0=EllipticCurve(K,witness['curve_ainvs'])
    P=E0(*(sage_eval(s,locals={'u':u}) for s in witness['generator']))
    assert P.order()==432
    a=witness['frobenius_eigenvalue_mod_432']
    assert a==145 and pow(a,3,432)==1 and pow(a,1,432)!=1 and pow(a,2,432)!=1
    assert E0(P[0]**p,P[1]**p)==a*P
    assert E0(P[0]**(p**2),P[1]**(p**2))!=P
    assert E0(P[0]**(p**3),P[1]**(p**3))==P
    assert [r['embedding_index'] for r in rows]==[0,1,2]
    assert all(r['status']=='PASS_CUBIC_GENERATOR_FORWARD' for r in rows)
    assert len({tuple(r['B_point']) for r in rows})==1
    assert len({tuple(r['E_point']) for r in rows})==1
    assert all(r['B_point']==[216,882] and r['E_point']==[130,407] for r in rows)
    assert all(not r['in_rational_generator_image'] for r in rows)
    F=GF(p)
    E=EllipticCurve(F,[0,0,0,0,432])
    B=EllipticCurve(F,[0,0,0,0,-16])
    H=E(130,407)
    Q=B(216,882)
    assert Q.order()==133
    assert E((Q[0]**3-64)/Q[0]**2,Q[1]*(Q[0]**3+128)/Q[0]**3)==H
    assert str([216,882]) not in prior['B_image_fiber_counts']
    out={'status':'PASS_CUBIC_WITNESS_AUDIT',
         'generator_degree_exact':3,'frobenius_scalar':a,
         'embeddings_checked':3,'B_point':[216,882],
         'E_point':[130,407],'B_point_order':133,
         'outside_rational_generator_image':True}
    (HERE/'extension_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':
    main()
