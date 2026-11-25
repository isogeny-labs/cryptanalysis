"""Evaluate the new nonrational-generator cyclic 432-subgroup."""
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, sage_eval

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


moduli=load('moduli',ROOT/'hecke-432-moduli-shift-evaluator-20261025'/'produce_sage.py')
bridge=load('bridge',ROOT/'hecke-27-coordinate-bridge-20261025'/'evaluate_sage.py')


def main():
    witness=json.loads((HERE/'extension_search.json').read_text())['witness']
    assert witness is not None
    maps=json.loads((ROOT/'hecke-27-coordinate-bridge-20261025'/'coordinate_map.json').read_text())
    previous=json.loads((HERE/'forward_census.json').read_text())
    p=883
    F=GF(p)
    K=GF(p**2,'u')
    u=K.gen()
    E0=EllipticCurve(K,witness['curve_ainvs'])
    P=E0(*(sage_eval(s,locals={'u':u}) for s in witness['generator']))
    assert P.order()==432
    frob=E0(P[0]**p,P[1]**p)
    assert frob==217*P and frob!=P and frob!=-P
    q=E0.isogeny(108*P)
    assert q.degree()==4
    M=q.codomain()
    S=q(P)
    R=27*S
    assert S.order()==108 and R.order()==4
    assert all(c**p==c for c in M.ainvs())
    assert S[0]**p==S[0] and S[1]**p==S[1]
    T0=moduli.dual_kernel_generator(q,E0,P)
    i=K(-1).sqrt()
    T=T0 if R.weil_pairing(T0,4)==i else -T0
    assert R.weil_pairing(T,4)==i
    plus,minus=moduli.shifted_pair(M,S,T)
    C=EllipticCurve(K,maps['curve_ainvs'])
    outputs=[]
    points=[]
    for label,(phi,C27) in (('plus',plus),('minus',minus)):
        js=phi.codomain().j_invariant()
        jt=phi.codomain().isogeny(C27).codomain().j_invariant()
        eliminant,candidates=bridge.roots_for_pair(C,maps,js,jt)
        assert len(candidates)==1
        points.append(candidates[0])
        outputs.append({'shift':label,'j_source':str(js),'j_target':str(jt),
                        'C_point':[str(candidates[0][0]),str(candidates[0][1])],
                        'coordinate_fiber_size':len(candidates)})
    assert points[0][0]**p==points[1][0] and points[0][1]**p==points[1][1]
    D=points[0]-points[1]
    xE,yE=-4*D[0],-8*i*(D[1]+K(1)/2)
    assert xE**p==xE and yE**p==yE
    E=EllipticCurve(F,[0,0,0,0,432])
    B=EllipticCurve(F,[0,0,0,0,-16])
    H=E(F(xE),F(yE))
    preimages=bridge.dual_preimages(H,B,E)
    assert len(preimages)==1
    Q=preimages[0]
    assert bridge.dual_image(Q,E)==H
    key=str([int(Q[0]),int(Q[1])]) if not Q.is_zero() else 'O'
    result={'status':'PASS_EXTENSION_GENERATOR_FORWARD',
            'input_curve_j':witness['curve_j'],'input_generator':witness['generator'],
            'frobenius_eigenvalue':217,'outputs':outputs,
            'E_point':[int(H[0]),int(H[1])],
            'B_point':[int(Q[0]),int(Q[1])] if not Q.is_zero() else 'O',
            'B_point_order':int(Q.order()),
            'in_rational_generator_image':key in previous['B_image_fiber_counts']}
    (HERE/'extension_evaluation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','B_point','B_point_order','in_rational_generator_image')},sort_keys=True))


if __name__=='__main__':
    main()
