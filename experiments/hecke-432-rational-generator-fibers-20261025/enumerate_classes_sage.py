"""Census all F_883 isomorphism classes with rational order-432 generators."""
import json
from pathlib import Path

from sage.all import EllipticCurve, EllipticCurve_from_j, GF

HERE = Path(__file__).resolve().parent


def text_point(P):
    return [int(P[0]), int(P[1])]


def subgroup_representatives(E, order):
    seen = set()
    reps = []
    for P in E.points():
        if P in seen or P.is_zero():
            continue
        if P.order() != order:
            continue
        subgroup = frozenset(k*P for k in range(order))
        assert len(subgroup) == order
        seen.update(subgroup)
        reps.append(P)
    return reps


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_CLASS_CENSUS'
    p = protocol['prime']
    assert p == 883
    F = GF(p)
    primitive = F.multiplicative_generator()
    nonsquare = primitive
    assert not nonsquare.is_square()
    target_order = 864
    classes = []
    j_counts = {'generic':0, 'j0':0, 'j1728':0}
    for j in F:
        if j == 0:
            variants = [(f'sextic_{k}',EllipticCurve(F,[0,0,0,0,primitive**k])) for k in range(6)]
            family='j0'
        elif j == F(1728):
            variants = [(f'quartic_{k}',EllipticCurve(F,[0,0,0,primitive**k,0])) for k in range(2)]
            family='j1728'
        else:
            E0 = EllipticCurve_from_j(j)
            variants = [('base',E0),('quadratic_twist',E0.quadratic_twist(nonsquare))]
            family='generic'
        j_counts[family] += 1
        for label,E in variants:
            count = int(E.cardinality())
            if count != target_order:
                continue
            reps = subgroup_representatives(E,protocol['required_rational_generator_order'])
            classes.append({'j':int(j),'family':family,'twist':label,
                            'curve_ainvs':[int(c) for c in E.ainvs()],
                            'curve_order':count,'rational_order_432_subgroups':len(reps),
                            'subgroup_generators':[text_point(P) for P in reps]})
        if int(j)%100==0:
            print(f'j={int(j)} classes={len(classes)}', flush=True)
    assert j_counts == {'generic':p-2,'j0':1,'j1728':1}
    out={'status':'COMPLETE_F883_CLASS_CENSUS', 'prime':p,
         'target_order':target_order,'j_classes_scanned':j_counts,
         'isomorphism_classes_with_order_864':len(classes),
         'classes_with_rational_order_432_subgroup':sum(r['rational_order_432_subgroups']>0 for r in classes),
         'rational_order_432_subgroups':sum(r['rational_order_432_subgroups'] for r in classes),
         'classes':classes}
    (HERE/'class_census.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','isomorphism_classes_with_order_864',
          'classes_with_rational_order_432_subgroup','rational_order_432_subgroups')},sort_keys=True))


if __name__=='__main__':
    main()
