"""Evaluate the F997 cyclic-chain census through the E projection."""
import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, GF, QQ
from sage.schemes.elliptic_curves.hom_composite import EllipticCurveHom_composite

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
spec=importlib.util.spec_from_file_location('kernel883',ROOT/'hecke-432-kernel-transport-20261025'/'evaluate_sage.py')
kernel=importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)


def value_at(map_data, P, field):
    def polynomial(terms):
        return sum(field(QQ(t['coefficient']))*P[0]**t['x_power']*P[1]**t['y_power']
                   for t in terms)
    denominator=polynomial(map_data['denominator'])
    numerator=polynomial(map_data['numerator'])
    assert denominator != 0
    return -numerator/denominator


def one(p, model, edges2, edges3, coordinate_map, intermediate_map):
    K=GF(p**2,'u')
    E=EllipticCurve(K,model)
    _,two_maps=kernel.chain(E,edges2)
    three,_=kernel.chain(E,edges3)
    q=EllipticCurveHom_composite.from_factors(two_maps[:2])
    psi=EllipticCurveHom_composite.from_factors(two_maps[2:])
    qdual=EllipticCurveHom_composite.from_factors([two_maps[1].dual(),two_maps[0].dual()])
    middle=q.codomain()
    R=kernel.order_four_kernel_generator(psi)
    T0=kernel.order_four_kernel_generator(qdual)
    i=K(-1).sqrt()
    T=T0 if R.weil_pairing(T0,4)==i else -T0
    assert R.weil_pairing(T,4)==i
    cpoly=q.push_subgroup(three.kernel_polynomial())
    assert cpoly.degree()==13 and cpoly.is_squarefree()
    C=EllipticCurve(K,coordinate_map['curve_ainvs'])
    choices=[]
    raw_counts=[]
    for Q4 in (T+R,T-R):
        phi=middle.isogeny(Q4)
        pushed=phi.push_subgroup(cpoly)
        assert pushed.degree()==13 and pushed.is_squarefree()
        quotient=phi.codomain().isogeny(pushed)
        _,points=kernel.roots_for_pair(C,coordinate_map,
                                       phi.codomain().j_invariant(),
                                       quotient.codomain().j_invariant())
        assert points
        raw_counts.append(len(points))
        three_kernel=pushed.gcd(phi.codomain().division_polynomial(3))
        assert three_kernel.degree()==1
        first=phi.codomain().isogeny(three_kernel)
        pushed9=first.push_subgroup(pushed)
        assert pushed9.degree()==4
        nine_kernel=pushed9.gcd(first.codomain().division_polynomial(3))
        assert nine_kernel.degree()==1
        second=first.codomain().isogeny(nine_kernel)
        actual_j3=first.codomain().j_invariant()
        actual_j9=second.codomain().j_invariant()
        points=[P for P in points
                if value_at(intermediate_map['j3'],P,K)==actual_j3
                and value_at(intermediate_map['j9'],P,K)==actual_j9]
        assert len(points)==1,(len(points),raw_counts[-1])
        choices.append(points)
    F=GF(p)
    Et=EllipticCurve(F,[0,0,0,0,432])
    B=EllipticCurve(F,[0,0,0,0,-16])
    projections=[]
    pair_count=0
    for Pplus in choices[0]:
        for Pminus in choices[1]:
            # i is rational when p = 1 (mod 4); each shifted map is then
            # Frobenius-fixed rather than exchanged with the other shift.
            if Pplus[0]**p!=Pplus[0] or Pplus[1]**p!=Pplus[1]:
                continue
            if Pminus[0]**p!=Pminus[0] or Pminus[1]**p!=Pminus[1]:
                continue
            pair_count+=1
            D=Pplus-Pminus
            if D.is_zero():
                H=Et(0)
            else:
                xe,ye=-4*D[0],-8*i*(D[1]+K(1)/2)
                assert xe**p==xe and ye**p==ye
                H=Et(F(xe),F(ye))
            preimages=([B(0)]+B.lift_x(F(0),all=True) if H.is_zero()
                       else kernel.dual_preimages(H,B,Et))
            assert len(preimages)==3
            assert all(kernel.dual_image(Q,Et)==H for Q in preimages)
            bkeys=[None if Q.is_zero() else (int(Q[0]),int(Q[1]))
                   for Q in preimages]
            projections.append({
                'E_point':None if H.is_zero() else [int(H[0]),int(H[1])],
                'B_preimages':[None if Q is None else list(Q)
                               for Q in sorted(bkeys,key=lambda x:(x is not None,x))]})
    assert pair_count==len(projections)==1
    return {'coordinate_counts':raw_counts,
            'intermediate_filtered_counts':[len(x) for x in choices],
            'frobenius_pair_count':pair_count,
            'projections':projections}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--limit',type=int)
    args=parser.parse_args()
    p=997
    census=json.loads((HERE/'census.json').read_text())
    maps=json.loads((ROOT/'hecke-27-coordinate-bridge-20261025'/'coordinate_map.json').read_text())
    intermediate=json.loads((HERE/'intermediate_j.json').read_text())
    rows=[]
    for source in census['rows']:
        for i,e2 in enumerate(source['two_paths']):
            for j,e3 in enumerate(source['three_paths']):
                if args.limit is not None and len(rows)>=args.limit:
                    break
                value=one(p,source['curve_ainvs'],e2,e3,maps,intermediate)
                rows.append({'source_j':source['j'],'source_ainvs':source['curve_ainvs'],
                             'source_label':source['label'],'pair':[i,j],**value})
                if len(rows)%50==0:
                    print(json.dumps({'completed':len(rows),'source_j':source['j']}),flush=True)
            if args.limit is not None and len(rows)>=args.limit:
                break
        if args.limit is not None and len(rows)>=args.limit:
            break
    out={'status':'COMPLETE_F997_E_PROJECTION','prime':p,'rows':rows,
         'row_count':len(rows),'candidate_count_distribution':dict(Counter(len(r['projections']) for r in rows))}
    target='image_probe.json' if args.limit is not None else 'image.json'
    (HERE/target).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','row_count','candidate_count_distribution')},sort_keys=True))


if __name__=='__main__':
    main()
