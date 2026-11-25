"""Independent exact group and fiber audit of the rational-generator image."""
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE=Path(__file__).resolve().parent


def subgroup_generated(points, curve):
    span={curve(0)}
    for P in points:
        orbit={k*P for k in range(P.order())}
        span={A+B for A in span for B in orbit}
    return span


def main():
    census=json.loads((HERE/'class_census.json').read_text())
    forward=json.loads((HERE/'forward_census.json').read_text())
    assert census['rational_order_432_subgroups']==54
    assert len(forward['rows'])==54
    F=GF(883)
    B=EllipticCurve(F,[0,0,0,0,-16])
    all_B=set(B.points())
    assert len(all_B)==forward['B_point_count']==931
    tally=Counter()
    inputs=set()
    for row in forward['rows']:
        assert row['status']=='PASS_FULL_FORWARD'
        E=EllipticCurve(F,row['input_ainvs'])
        P=E(row['input_generator'])
        assert E.cardinality()==864 and P.order()==432
        subgroup=frozenset(k*P for k in range(432))
        key=(tuple(row['input_ainvs']),subgroup)
        assert key not in inputs
        inputs.add(key)
        xy=row['B_point']
        assert xy!='O'
        Q=B(xy)
        tally[Q]+=1
    assert len(inputs)==54
    assert len(tally)==forward['distinct_B_images']==12
    assert sum(tally.values())==54
    recorded=Counter({B(json.loads(key)):count for key,count in forward['B_image_fiber_counts'].items()})
    assert tally==recorded
    span=subgroup_generated(list(tally),B)
    missing=all_B-set(tally)
    assert len(missing)==919
    order_counts=Counter(int(Q.order()) for Q in tally)
    fiber_counts=Counter(tally.values())
    out={'status':'PASS_EXACT_RESTRICTED_IMAGE_AUDIT','prime':883,
         'B_point_count':len(all_B),'distinct_image_points':len(tally),
         'points_outside_rational_generator_image':len(missing),
         'input_subgroups_replayed':len(inputs),
         'image_point_order_histogram':dict(sorted(order_counts.items())),
         'fiber_multiplicity_histogram':dict(sorted(fiber_counts.items())),
         'subgroup_generated_by_image_size':len(span),
         'image_fraction_exact':f'{len(tally)}/{len(all_B)}'}
    (HERE/'coverage_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':
    main()
