"""Audit the F887 source count, resolved modular image, and cusp gap."""
import json
from collections import Counter
from math import gcd
from pathlib import Path

HERE=Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE/name).read_text())


def main():
    p=887
    census=read('census.json')
    resolved=read('image.json')
    coarse=read('image_jpair_only.json')
    intermediate=read('intermediate_j.json')
    assert census['j_values_scanned']==p
    assert census['raw_chain_pairs']==888
    assert census['X0_point_count_from_Hecke']==880
    assert sum(r['paired_chain_count'] for r in census['rows']
               if r['label'] in ('j0_twist','j1728_twist'))==16
    assert len(resolved['rows'])==len(coarse['rows'])==872
    expected=[(tuple(r['curve_ainvs']),(i,j)) for r in census['rows']
              if r['label'] not in ('j0_twist','j1728_twist')
              for i in range(len(r['two_paths']))
              for j in range(len(r['three_paths']))]
    actual=[(tuple(r['source_ainvs']),tuple(r['pair'])) for r in resolved['rows']]
    assert expected==actual and len(set(actual))==872
    assert all(len(r['B_candidates'])==1 and r['B_candidates'][0] is not None
               and r['intermediate_filtered_counts']==[1,1] for r in resolved['rows'])
    assert all((r['B_candidates'][0][1]**2-r['B_candidates'][0][0]**3+16)%p==0
               for r in resolved['rows'])
    assert Counter(len(r['B_candidates']) for r in coarse['rows'])=={1:792,2:64,3:16}
    assert all(intermediate[f'j{k}']['training_nullity']==1
               and intermediate[f'j{k}']['holdout_zero'] for k in (3,9))
    fibers=Counter(tuple(r['B_candidates'][0]) for r in resolved['rows'])
    hist=Counter(fibers.values())
    assert len(fibers)==109 and hist=={6:1,7:2,8:102,9:4}
    assert sum(n*c for n,c in hist.items())==872
    def phi(n):
        return sum(gcd(k,n)==1 for k in range(1,n+1))
    cusps=sum(phi(gcd(d,432//d)) for d in range(1,433)
              if 432%d==0 and (p-1)%gcd(d,432//d)==0)
    assert cusps==8 and census['X0_point_count_from_Hecke']-cusps==872
    squares=Counter(y*y%p for y in range(p))
    B_order=1+sum(squares[(x*x*x-16)%p] for x in range(p))
    assert B_order==888
    out={'status':'PASS_F887_IMAGE_AUDIT','prime':p,
         'X0_rational_points':880,'rational_cusps':cusps,
         'noncuspidal_source_points':872,
         'B_group_order':B_order,'noncuspidal_B_images':len(fibers),
         'identity_in_noncuspidal_image':False,
         'whole_curve_B_images':len(fibers)+1,
         'B_points_outside_whole_curve_image':B_order-len(fibers)-1,
         'fiber_size_distribution':{str(k):v for k,v in sorted(hist.items())},
         'j_pair_only_candidate_count_distribution':{'1':792,'2':64,'3':16}}
    (HERE/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':
    main()
