"""Exact cusp fields and split-prime torsion controls for the level-432 map."""
import json
from math import gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = 883
N = 432


def phi(n):
    return sum(gcd(k,n)==1 for k in range(1,n+1))


def divisors(n):
    return [d for d in range(1,n+1) if n%d == 0]


def curve_points(q):
    return [(x,y) for x in range(q) for y in range(q)
            if (y*y-x*x*x+16)%q == 0]


def main():
    cusp_rows=[]
    for d in divisors(N):
        h=gcd(d,N//d)
        cusp_rows.append({'denominator':d,'h':h,'geometric_cusps':phi(h),
                          'F883_rational':(P-1)%h==0})
    geometric=sum(r['geometric_cusps'] for r in cusp_rows)
    rational=sum(r['geometric_cusps'] for r in cusp_rows if r['F883_rational'])
    assert geometric==36 and rational==24
    assert all(r['h'] in (1,2,3,6) for r in cusp_rows if r['F883_rational'])
    reductions={str(q):{'point_count':len(curve_points(q))+1,'finite_points':curve_points(q),
                        'split_root_of_zeta3_polynomial':
                        next(z for z in range(q) if (z*z+z+1)%q==0)} for q in (7,13)}
    assert reductions['7']['point_count']==7 and reductions['13']['point_count']==9
    old=json.loads((HERE.parent/'hecke-432-kernel-transport-20261025'/'audit.json').read_text())
    assert old['distinct_B_images']==36 and old['B_group_order']==931
    out={'status':'PASS_CUSP_FIELD_AND_TORSION_CONTROL','level':N,'prime':P,
         'geometric_cusps':geometric,'F883_rational_cusps':rational,
         'rational_cusp_field_contained_in':'Q(zeta_6)=Q(sqrt(-3))',
         'cusp_rows':cusp_rows,'split_good_reductions':reductions,
         'B_over_cusp_field_torsion_order':1,
         'conditional_whole_curve_image_if_normalized_map':37,
         'conditional_B_points_outside_whole_curve_image':894,
         'remaining_bridge':'verify that the implemented quarter-shift map extends over Q and maps the infinity cusp to B identity'}
    (HERE/'result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','geometric_cusps','F883_rational_cusps',
                                       'B_over_cusp_field_torsion_order',
                                       'conditional_whole_curve_image_if_normalized_map')},sort_keys=True))


if __name__=='__main__':
    main()
