#!/usr/bin/env python3
"""Recompute fixed-input pipeline diagnostics without granting timing standing."""
import hashlib
import argparse
import json
import math
from pathlib import Path
import statistics
import random

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='timing-001');parser.add_argument('--stem',default='analysis');args=parser.parse_args()
assert args.run_id.replace('-','').isalnum() and args.stem.replace('-','').isalnum()
OUT=HERE/args.run_id


def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def report(row):return row.get('result',{}).get('report',{}).get('Ok')
def median(v):return statistics.median(v) if v else None


pairs=json.loads((OUT/'triples.json').read_text())
references=json.loads((OUT/'references.json').read_text())
summary=json.loads((OUT/'summary.json').read_text())
identities=json.loads((HERE/'identities.json').read_text())
instances=json.loads((HERE/'instances.json').read_text())
ref_by_key={(r['index'],r['fixture']):r for r in references}
errors=[];rows=[]
if summary['status']!='matrix_completed_unqualified' or len(pairs)!=120 or len(references)!=120:errors.append('incomplete frozen panel')
if {(p['index'],p['fixture']) for p in pairs}!={(i,f) for i in range(5) for f in range(320,344)}:errors.append('frozen fixture coverage mismatch')
for p in pairs:
 row={k:p[k] for k in ['index','fixture','order','candidate_ids','workload']}
 wid=p['workload'];workload=json.loads((ROOT/'experiments/ic-bench/workloads'/f'{wid}.json').read_text())
 assert digest(workload).startswith(wid)
 assert workload['target_count']==1
 expected_scalar,x,y=workload['targets'][0]
 matched=ref_by_key.get((p['index'],p['fixture']),{}).get('result')
 row['reference_completed']=bool(matched and all(matched[k]['verified'] and matched[k]['recovered']==expected_scalar for k in ['plain','matched']))
 for variant in ['mitm-prefix','mitm-prefix64','mitm-vector','mitm-vector64']:
  raw=p['runs'][variant];r=report(raw);rdata=raw.get('result')
  value={'exit_code':raw['exit_code'],'completed':r is not None,'verified':bool(r and r['verified']),
         'peak_rss_kib':raw.get('peak_rss_kib'),'child_rusage':raw.get('child_rusage'),'candidate_id':p['candidate_ids'][variant],'run_id':p['candidate_ids'][variant]+'W'+wid+'R001'}
  candidate=json.loads((ROOT/'experiments/ic-bench/candidates'/f"{value['candidate_id']}.json").read_text())
  assert digest(candidate).startswith(value['candidate_id'].rsplit('h',1)[1])
  if rdata:
   frozen=json.loads((OUT/f"calibration-{p['index']}.json").read_text())['calibration']
   assert rdata['calibration']==frozen
   correct_input=(rdata['curve_id']==workload['curve_id'] and rdata['planted']==expected_scalar
                  and rdata['target']==[x,y] and rdata['target_seed']==workload['walk_seed'])
   value['input_matches_manifest']=correct_input
   if not correct_input:errors.append('input mismatch '+value['run_id'])
  if r:
   if raw.get('parse_error') or 'child_rusage' not in raw:errors.append('missing rusage '+value['run_id'])
   assert r['decomposition']['name']==candidate['point_decomposition']['oracle'], 'oracle routing mismatch'
   setup=r['decomposition']['setup'];ns=setup['native'].get('mitm_native_setup_ns',setup['native'].get('mitm_batch_setup_ns',0))
   assert ns>0 and setup['group_ops']==dict(adds=0,doubles=0,scalar_mults=0)
   assert abs(setup['gae']-ns/rdata['calibration']['ns_per_add'])<1e-7*max(setup['gae'],1)
   assert not rdata['euclidean_inverse']
   if 'vector' in variant:assert setup['native']['mitm_vector_pairs']>0, 'vector path not exercised'
   else:assert setup['native']['mitm_vector_pairs']==0
   assert setup['native']['mitm_vector_pclmul128_pairs']+setup['native']['mitm_vector_vpclmul_pairs']==setup['native']['mitm_vector_pairs']
   for key,expected in candidate['point_decomposition']['params'].items():assert int(r['spec']['oracle_params'][key])==expected, 'parameter routing mismatch'
   assert r['factor_base']['signed_points']==candidate['factor_base']['actual_usable_point_count']
   assert r['factor_base']['columns']==candidate['factor_base']['effective_columns']
   if r['verified'] and r['recovered']!=expected_scalar:errors.append('wrong scalar '+value['run_id'])
   ns_add=rdata['calibration']['ns_per_add'];root_r=math.sqrt(r['r'])
   phases=[r['factor_base']['cost'],r['decomposition']['setup'],r['decomposition']['cost'],r['linear_algebra']['cost'],r['verify']]
   total=sum(phase['gae'] for phase in phases)
   assert abs(total-r['total_gae'])<=1e-8*max(total,1)
   assert abs(r['s']-total/root_r)<=1e-8*max(r['s'],1)
   cold_ns=rdata['context_ns']+r['wall_seconds']*1e9
   value.update({'pipeline_wall_s':r['wall_seconds'],'cold_wall_s':cold_ns*1e-9,
                 'counted_s':r['s'],'context_inclusive_counted_s':r['s']+rdata['context_ns']/ns_add/root_r,
                 'wall_derived_s':cold_ns/ns_add/root_r,
                 'targets_tried':r['decomposition']['targets_tried'],'relations':r['decomposition']['relations_found'],
                 'rank':r['linear_algebra']['rank'],'solver_ns':(r['decomposition']['solver'] or {}).get('wall_ns',0),
                 'descent_ns':sum(phase.get('native',{}).get('symbolic_descent_ns',0) for phase in phases),
                 'native_affine_ns':sum(phase.get('native',{}).get('affine_s3_ns',0) for phase in phases),
                 'oracle_setup_ns':r['decomposition']['setup'].get('native',{}),
                 'oracle_query_native':r['decomposition']['cost'].get('native',{}),
                 'exhausted':r['exhausted']})
   if row['reference_completed']:
    assert matched['target']==[x,y] and matched['target_seed']==workload['walk_seed']
    rho=matched['matched'];rho_add=matched['calibration']['ns_per_add']
    rho_counted=rho['s']+matched['context_ns']/rho_add/root_r
    rho_wall=(rho['wall_ns']+matched['context_ns'])*1e-9
    value['context_counted_gap_to_matched_rho']=value['context_inclusive_counted_s']/rho_counted
    value['cold_wall_gap_to_matched_rho']=value['cold_wall_s']/rho_wall
  row[variant]=value
 a,b,c,d=(row[v] for v in ['mitm-prefix','mitm-prefix64','mitm-vector','mitm-vector64'])
 valid=all(v['verified'] and v.get('input_matches_manifest') for v in [a,b,c,d])
 if not valid or not row['reference_completed']:errors.append(f"incomplete or invalid answers {p['index']}/{p['fixture']}")
 row['valid_paired_answers']=valid
 row['same_counts']=p.get('batch_preserves_counts')
 if not p.get('same_calibration'):errors.append(f"model unit mismatch {p['index']}/{p['fixture']}")
 row['calibration_ratio']=p.get('calibration_ratio')
 row['calibration_within_bound']=p.get('calibration_within_bound')
 if valid:
  if not p.get('batch_preserves_counts'):errors.append(f"same-method count mismatch {p['index']}/{p['fixture']}")
  row['raw_cold_ratios']={m:a['cold_wall_s']/row[m]['cold_wall_s'] for m in ['mitm-prefix64','mitm-vector','mitm-vector64']}
  row['raw_counted_s_ratios']={m:a['context_inclusive_counted_s']/row[m]['context_inclusive_counted_s'] for m in ['mitm-prefix64','mitm-vector','mitm-vector64']}
 row['qualified']=None
 rows.append(row)
cases=[]
for index in range(5):
 for method in ['mitm-prefix64','mitm-vector','mitm-vector64']:
  selected=[r for r in rows if r['index']==index]
  valid=[r for r in selected if r['valid_paired_answers']]
  case={'index':index,'curve_id':instances[index]['curve_id'],'method':method,'attempted_pairs':len(selected),
        'valid_pairs':len(valid),'expected_pairs':24,'qualification':None,
        'capped_arms':sum(r[v]['exit_code']==124 for r in selected for v in ['mitm-prefix','mitm-prefix64','mitm-vector','mitm-vector64']),
        'calibration_failures':sum(r['calibration_within_bound'] is False for r in selected),
        'all_frozen_pairs_valid':len(valid)==24}
  # Headline medians require every frozen pair; partial ratios stay in raw rows.
  if len(valid)==24:
   case['raw_cold_median_ratio']=median([r['raw_cold_ratios'][method] for r in valid])
   rng=random.Random(20261116);values=[r['raw_cold_ratios'][method] for r in valid]
   boot=sorted(median(rng.choices(values,k=24)) for _ in range(10000))
   def quantile(q):
    x=q*(len(boot)-1);i=int(x);return boot[i]+(boot[min(i+1,len(boot)-1)]-boot[i])*(x-i)
   case['raw_cold_paired_median_bootstrap95']=[quantile(.025),quantile(.975)]
   case['bootstrap_scope']='exploratory; frozen10000/seed20261116, all rows retained'
   case['raw_counted_s_median_ratio']=median([r['raw_counted_s_ratios'][method] for r in valid])
  for v in ['mitm-prefix','mitm-prefix64','mitm-vector','mitm-vector64']:
   case[v+'_verified_answers']=sum(r[v]['verified'] for r in selected)
   if len(valid)==24:
    case[v+'_mean_cold_wall_s']=statistics.mean(r[v]['cold_wall_s'] for r in valid)
    peaks=[r[v]['peak_rss_kib'] for r in valid if r[v]['peak_rss_kib'] is not None]
    case[v+'_max_reported_peak_rss_kib']=max(peaks) if len(peaks)==24 else None
   if len(valid)==24:
    for metric in ['cold_wall_s','context_inclusive_counted_s','solver_ns','descent_ns',
                   'context_counted_gap_to_matched_rho','cold_wall_gap_to_matched_rho']:
     values=[r[v][metric] for r in valid if metric in r[v]]
     case[v+'_median_'+metric]=median(values) if len(values)==24 else None
  cases.append(case)
result={'schema':'ic-affine-pipeline-analysis/v1','status':'pass' if not errors else 'fail','errors':errors,
        'run_status':summary['status'],'pairs':len(rows),'references':len(references),
        'timing_qualified':False,'qualified':None,'cases':cases,'rows':rows}
(HERE/(args.stem+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
if errors:raise SystemExit(1)
