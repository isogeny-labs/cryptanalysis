"""Exact target-orbit coverage ceilings for fixed-prefix W23 relation search."""
import hashlib
import json
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'protocol.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
assert sha(HERE/'run.py')==protocol['runner_sha256']
getcontext().prec=70
def fraction(q):return {'numerator':str(q.numerator),'denominator':str(q.denominator),
                        'decimal':str(Decimal(q.numerator)/Decimal(q.denominator))}
def ceildiv(a,b):return (a+b-1)//b
n131=json.loads((ROOT/'n131_w23_sixpair_density_20261016/projection_result.json').read_text())
census=json.loads((ROOT/'n131_w23_sixpair_density_20261016/run_result.json').read_text())
independent=json.loads((ROOT/'n131_w23_sixpair_density_20261016/audit_result.json').read_text())
assert census['worker_result']['usable_edges']==independent['worker_result']['usable_edges']==n131['usable_edges_per_slot']==1049218
r=int(n131['subgroup_order_r']);M=4*n131['usable_edges_per_slot'];orbit=131
assert r==680564733841876926932320129493409985129 and M==4196872
rows=[]
for free in range(2,7):
    labels=orbit*M**free
    half_subgroup=ceildiv(r,2*labels)
    half_uniform_raw=ceildiv(4*r,2*labels)
    rows.append({'free_slots':free,'fixed_slots':6-free,'signed_state_ceiling_per_free_slot':M,
                 'labeled_orbit_emissions_per_fixed_prefix':str(labels),
                 'subgroup_reach_ceiling_per_fixed_prefix':fraction(min(Fraction(1),Fraction(labels,r))),
                 'uniform_random_raw_reach_ceiling_per_fixed_prefix':fraction(min(Fraction(1),Fraction(labels,4*r))),
                 'prefixes_before_subgroup_union_bound_allows_half':str(half_subgroup),
                 'prefixes_before_uniform_raw_union_bound_allows_half':str(half_uniform_raw),
                 'subgroup_prefixes_per_second_for_600s':fraction(Fraction(half_subgroup,600)),
                 'uniform_raw_prefixes_per_second_for_600s':fraction(Fraction(half_uniform_raw,600))})
lower=int(n131['signed_sixpair_tuples_lower']);upper=int(n131['signed_sixpair_tuples_upper'])
all_raw_mean=[Fraction(orbit*x,r) for x in (lower,upper)]
one_random_raw_mean=[Fraction(orbit*x,4*r) for x in (lower,upper)]
n41=json.loads((ROOT/'n41_w8_sixpair_sat_20261016/source_count_result.json').read_text())
join=json.loads((ROOT/'n41_sixpair_target_orbit_20261016/join_result.json').read_text())
audit=json.loads((ROOT/'n41_sixpair_target_orbit_20261016/join_audit.json').read_text())
r41=549756390943
assert n41['signed_sixpair_tuples']==n41['ordered_six_edge_tuples']*4**6
assert len(join['hits'])==audit['relation_count']==audit['final_rank']==41
first_states={int(line.split()[2]) for line in join['hits']}
result={'status':'COMPLETE_W23_TARGET_ORBIT_RESIDUAL_COVERAGE_BOUND','candidate_id':None,
        'field_degree':131,'subgroup_order':str(r),'raw_curve_order':str(4*r),
        'target_orbit_size':orbit,'usable_edges_per_slot':n131['usable_edges_per_slot'],
        'signed_states_per_slot':M,'rows':rows,
        'all_four_raw_preimages_orbit_sum_uniform_subgroup_mean_bounds':list(map(fraction,all_raw_mean)),
        'one_uniformly_random_raw_preimage_orbit_sum_mean_bounds':list(map(fraction,one_random_raw_mean)),
        'n41_control':{'source_signed_tuples':str(n41['signed_sixpair_tuples']),
                       'one_random_raw_orbit_mean':fraction(Fraction(41*n41['signed_sixpair_tuples'],4*r41)),
                       'first_hit_orbit_positions':len(join['hits']),
                       'first_hit_distinct_fixed_slot0_states':len(first_states),
                       'independent_relation_rank':audit['final_rank']},
        'protocol_sha256':sha(HERE/'protocol.json')}
(HERE/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'free5_half_subgroup':rows[3]['prefixes_before_subgroup_union_bound_allows_half'],
                  'free5_half_uniform_raw':rows[3]['prefixes_before_uniform_raw_union_bound_allows_half'],
                  'free4_half_subgroup':rows[2]['prefixes_before_subgroup_union_bound_allows_half'],
                  'n41_first_hit_states':len(first_states)},sort_keys=True))
