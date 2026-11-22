"""Match rational and cubic-generator witnesses to rational isogeny chains."""
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, sage_eval

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def point_chain(E,P,ell,depth,p):
    Q=(432//(ell**depth))*P
    assert Q.order()==ell**depth
    roots=[]
    codomain_js=[]
    for remaining in range(depth,0,-1):
        kernel=(ell**(remaining-1))*Q
        assert kernel.order()==ell
        x=kernel[0]
        assert x**p==x
        ring=PolynomialRing(E.base_field(),'z')
        phi=E.isogeny(ring.gen()-x)
        assert phi.degree()==ell and phi(kernel).is_zero()
        roots.append(int(x))
        E=phi.codomain()
        Q=phi(Q)
        codomain_js.append(int(E.j_invariant()))
    assert Q.is_zero()
    return {'kernel_x_sequence':roots,'target_j_sequence':codomain_js}


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    paths=json.loads((HERE/'chain_probe.json').read_text())['chains']
    census=json.loads((ROOT/'hecke-432-rational-generator-fibers-20261025'/'class_census.json').read_text())
    cubic=json.loads((ROOT/'hecke-432-rational-generator-fibers-20261025'/'extension3_search.json').read_text())['witness']
    j6=next(row for row in census['classes'] if row['j']==6)
    p=883
    witnesses=[]
    F=GF(p)
    E=EllipticCurve(F,j6['curve_ainvs'])
    P=E(j6['subgroup_generators'][0])
    witnesses.append(('rational',E,P))
    K3=GF(p**3,'u')
    u=K3.gen()
    E3=EllipticCurve(K3,cubic['curve_ainvs'])
    P3=E3(*(sage_eval(s,locals={'u':u}) for s in cubic['generator']))
    witnesses.append(('cubic',E3,P3))
    rows=[]
    for label,curve,point in witnesses:
        record={'witness':label,'generator_order':int(point.order()),'chains':{}}
        for ell,depth in ((2,4),(3,3)):
            chain=point_chain(curve,point,ell,depth,p)
            matches=[i for i,path in enumerate(paths[str(ell)]['paths']) if
                     chain['kernel_x_sequence']==[edge['kernel_x'] for edge in path] and
                     chain['target_j_sequence']==[edge['target_j'] for edge in path]]
            assert len(matches)==1
            chain['enumerated_path_index']=matches[0]
            record['chains'][str(ell)]=chain
        rows.append(record)
    assert rows[0]['chains']!=rows[1]['chains']
    out={'status':'PASS_WITNESS_CHAIN_MATCH','source_j':6,'witnesses':rows}
    (HERE/'witness_chain_validation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'path_pairs':[[r['chains']['2']['enumerated_path_index'],
                       r['chains']['3']['enumerated_path_index']] for r in rows]},sort_keys=True))


if __name__=='__main__':
    main()
