"""Independent exact-integer and frozen-source audit of the coverage receipt."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'protocol.json').read_text())
out=json.loads((HERE/'result.json').read_text())
assert out['protocol_sha256']==sha(HERE/'protocol.json')
assert protocol['runner_sha256']==sha(HERE/'run.py')
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
projection=json.loads((ROOT/'n131_w23_sixpair_density_20261016/projection_result.json').read_text())
source=json.loads((ROOT/'n41_w8_sixpair_sat_20261016/source_count_result.json').read_text())
join=json.loads((ROOT/'n41_sixpair_target_orbit_20261016/join_result.json').read_text())
r=int(projection['subgroup_order_r']);n=4*projection['usable_edges_per_slot'];j=projection['six_rotations']
assert len(j)==131//131*6 and out['target_orbit_size']==131
assert n==int(out['signed_states_per_slot'])==4196872
assert r==int(out['subgroup_order']) and 4*r==int(out['raw_curve_order'])
for row in out['rows']:
    h=row['free_slots'];labels=131*n**h
    assert h+row['fixed_slots']==6 and int(row['labeled_orbit_emissions_per_fixed_prefix'])==labels
    for key,denominator in [('subgroup_reach_ceiling_per_fixed_prefix',r),
                            ('uniform_random_raw_reach_ceiling_per_fixed_prefix',4*r)]:
        value=row[key]
        assert Fraction(int(value['numerator']),int(value['denominator']))==min(Fraction(1),Fraction(labels,denominator))
    for key,denominator in [('prefixes_before_subgroup_union_bound_allows_half',r),
                            ('prefixes_before_uniform_raw_union_bound_allows_half',4*r)]:
        k=int(row[key]);assert (k-1)*2*labels<denominator<=k*2*labels
for i,key in enumerate(('signed_sixpair_tuples_lower','signed_sixpair_tuples_upper')):
    label_count=int(projection[key])
    all_record=out['all_four_raw_preimages_orbit_sum_uniform_subgroup_mean_bounds'][i]
    one_record=out['one_uniformly_random_raw_preimage_orbit_sum_mean_bounds'][i]
    all_mean=Fraction(int(all_record['numerator']),int(all_record['denominator']))
    one_mean=Fraction(int(one_record['numerator']),int(one_record['denominator']))
    assert all_mean==Fraction(131*label_count,r) and one_mean==all_mean/4
assert source['signed_sixpair_tuples']==source['ordered_six_edge_tuples']*4**6
assert Fraction(source['uniform_raw_target_mean'])==Fraction(source['signed_sixpair_tuples'],4*549756390943)
assert len(join['hits'])==out['n41_control']['first_hit_orbit_positions']==41
assert len({int(line.split()[2]) for line in join['hits']})==out['n41_control']['first_hit_distinct_fixed_slot0_states']==35
assert out['n41_control']['independent_relation_rank']==41
lean=(HERE/'lean.stdout').read_text()
assert "'TargetOrbitCoverage.distinct_target_bound' depends on axioms: [propext]" in lean
assert 'sorryAx' not in lean and not (HERE/'lean.stderr').read_text()
receipt={'status':'PASS_W23_TARGET_ORBIT_COVERAGE_BOUND','candidate_id':None,
         'result_sha256':sha(HERE/'result.json'),'lean_sha256':sha(HERE/'lean.stdout'),
         'input_sha256':{path:sha(path) for path in protocol['sources']}}
(HERE/'terminal.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(receipt['status'])
