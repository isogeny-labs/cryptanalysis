#!/usr/bin/env python3
"""Audit routing and paired native collector diagnostics; never grant standing."""
import hashlib,itertools,json,math,random,statistics
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];OUT=P/'timing-001'
MODES=['mitm-walk-incumbent','mitm-walk16-scalar','mitm-walk16-native']
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def report(row):return row.get('result',{}).get('report',{}).get('Ok')
def med(v):return statistics.median(v) if v else None
def boot(values):
 rng=random.Random(20261116);v=sorted(statistics.median(rng.choices(values,k=len(values))) for _ in range(10000))
 def q(p):
  x=p*(len(v)-1);i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
 return [q(.025),q(.975)]
def signature(r):
 return [(p['group_ops'],{k:v for k,v in p['native'].items() if not k.endswith('_ns') and k not in ['walk_batch_native_requested','walk_batch_native_backend']}) for p in [r['decomposition']['cost'],r['linear_algebra']['cost'],r['verify']]]
triples=json.loads((OUT/'triples.json').read_text());refs=json.loads((OUT/'references.json').read_text());ids=json.loads((P/'identities.json').read_text());instances=json.loads((P/'instances.json').read_text());summary=json.loads((OUT/'summary.json').read_text())
prepared_receipt=json.loads((OUT/'preparation-receipt.json').read_text())
errors=[];rows=[];refmap={(x['index'],x['fixture']):x for x in refs}
if summary['status']!='matrix_completed_unqualified' or len(triples)!=120 or len(refs)!=120:errors.append('incomplete frozen panel')
if {(x['index'],x['fixture']) for x in triples}!={(i,f) for i in range(5) for f in range(384,408)}:errors.append('fixture coverage mismatch')
for triple in triples:
 index,fixture=triple['index'],triple['fixture'];row=dict(index=index,fixture=fixture,order=triple['order'],qualified=None,methods={})
 assert triple['order']==list(list(itertools.permutations(MODES))[(fixture-384)%6])
 wid=ids[str(index)]['workloads'][str(fixture)];workload=json.loads((ROOT/'experiments/ic-bench/workloads'/f'{wid}.json').read_text());assert digest(workload).startswith(wid)
 row['workload']=wid;scalar,x,y=workload['targets'][0];ref=refmap.get((index,fixture),{});reference={}
 frozen=json.loads((OUT/f'calibration-{index}.json').read_text())['calibration']
 assert all(frozen[k]>0 for k in ['ns_per_add','ns_per_double','ns_per_lookup','ns_per_row_op'])
 for name in ['rho-plain','rho-negation']:
  raw=ref.get('runs',{}).get(name,{});d=raw.get('result');s=(d or {}).get('solver')
  complete=bool(s and s['verified'] and s['recovered']==scalar and not d['euclidean_inverse'])
  reference[name]=dict(complete=complete,exit_code=raw.get('exit_code'),compute_s=d.get('reference_compute_through_cleanup_ns',0)*1e-9 if d else None,peak_rss_kib=raw.get('peak_rss_kib'))
  if d:
   assert d['curve_id']==workload['curve_id'] and d['target']==[x,y] and d['planted']==scalar and d['target_seed']==workload['walk_seed'] and d['calibration']==frozen
  if not complete:errors.append(f'incomplete reference {index}/{fixture}/{name}')
 row['references']=reference
 reports={}
 for mode in MODES:
  raw=triple['runs'][mode];d=raw.get('result');r=report(raw);cid=ids[str(index)][mode];candidate=json.loads((ROOT/'experiments/ic-bench/candidates'/f'{cid}.json').read_text());assert digest(candidate).startswith(cid.rsplit('h',1)[1]);assert candidate['implementation']['sources_sha256']==prepared_receipt['source_sha256']
  result=dict(candidate_id=cid,run_id=cid+'W'+wid+'R001',complete=bool(r and r['verified'] and r['recovered']==scalar),exit_code=raw['exit_code'],peak_rss_kib=raw.get('peak_rss_kib'),process_wall_s=raw.get('process_wall_s'),child_rusage=raw.get('child_rusage'))
  if d:
   assert all(d[k]==v for k,v in [('curve_id',workload['curve_id']),('planted',scalar),('target',[x,y]),('target_seed',workload['walk_seed']),('calibration',frozen)])
   assert not d['euclidean_inverse'] and d['mode']==mode
  if r:
   reports[mode]=r
   assert r['decomposition']['name']=='mitm-batched' and r['linear_algebra']['name']=='incremental-gauss'
   assert r['spec']['targets']=={'mitm-walk-incumbent':'Walk','mitm-walk16-scalar':'WalkBatchScalar','mitm-walk16-native':'WalkBatch'}[mode]
   assert r['spec']['max_trials']==500000
   assert r['factor_base']['signed_points']==candidate['factor_base']['actual_usable_point_count'] and r['factor_base']['columns']==candidate['factor_base']['effective_columns']
   for k,v in candidate['point_decomposition']['params'].items():assert int(r['spec']['oracle_params'][k])==v
   setup=r['decomposition']['setup'];native=setup['native'];query=r['decomposition']['cost']['native']
   assert native['mitm_vector_pairs']>0 and native['mitm_vector_packed_square_pairs']==0 and native['mitm_scalar_prepare']==0
   assert native['mitm_vector_pclmul128_pairs']+native['mitm_vector_vpclmul_pairs']==native['mitm_vector_pairs']
   assert setup['group_ops']==dict(adds=0,doubles=0,scalar_mults=0)
   assert abs(setup['gae']-native['mitm_batch_setup_ns']/frozen['ns_per_add'])<1e-7*max(1,setup['gae'])
   if mode!='mitm-walk-incumbent':
    flag=int(mode=='mitm-walk16-native');assert query['walk_batch_native_requested']==flag and query['walk_batch_native_backend']==flag
    assert query['walk_batch_lanes']==16 and query['walk_batch_pair_calls']>0 and query['walk_batch_pair_adds']>0
    assert query['walk_batch_generated']==query['walk_batch_consumed']+query['walk_batch_unused']<=500000
   compute=r['collector_wall_seconds'];through=d['computation_through_cleanup_ns']*1e-9
   assert 0<compute<=through and 'child_rusage' in raw
   phases=[r['factor_base']['cost'],setup,r['decomposition']['cost'],r['linear_algebra']['cost'],r['verify']]
   assert abs(sum(x['gae'] for x in phases)-r['total_gae'])<=1e-8*max(1,r['total_gae'])
   assert abs(r['s']-r['total_gae']/math.sqrt(r['r']))<=1e-8*max(1,r['s'])
   result.update(collector_s=compute,computation_through_cleanup_s=through,context_plus_computation_s=d['context_ns']*1e-9+through,context_s=d['context_ns']*1e-9,base_setup_s=r['factor_base']['cost']['wall_ns']*1e-9,oracle_setup_s=setup['wall_ns']*1e-9,query_counters=query,queries=r['decomposition']['targets_tried'],relations=r['decomposition']['relations_found'],rank=r['linear_algebra']['rank'],rows=r['linear_algebra']['rows'],matrix_work=r['linear_algebra']['work'],exhausted=r['exhausted'],reported_counted_s=r['s'])
   result['rho_over_ic']={k:v['compute_s']/compute for k,v in reference.items() if v['complete']}
  if not result['complete']:errors.append(f'incomplete IC {index}/{fixture}/{mode}')
  row['methods'][mode]=result
 if len(reports)==3:
  a,b=(reports[m] for m in MODES[1:]);equal=signature(a)==signature(b) and all(a[s][k]==b[s][k] for s,k in [('decomposition','targets_tried'),('decomposition','relations_found'),('linear_algebra','rank'),('linear_algebra','rows'),('linear_algebra','dependent'),('linear_algebra','work')])
  row['same_schedule_counts']=equal
  if not equal or not triple.get('same_schedule_counts'):errors.append(f'same-schedule count mismatch {index}/{fixture}')
 if all(row['methods'][m]['complete'] for m in MODES):
  row['ratios']={name:row['methods'][ref]['collector_s']/row['methods'][test]['collector_s'] for name,ref,test in [('native_vs_incumbent',MODES[0],MODES[2]),('native_vs_scalar_schedule',MODES[1],MODES[2]),('scalar_schedule_vs_incumbent',MODES[0],MODES[1])]}
  row['through_cleanup_ratios']={name:row['methods'][ref]['context_plus_computation_s']/row['methods'][test]['context_plus_computation_s'] for name,ref,test in [('native_vs_incumbent',MODES[0],MODES[2]),('native_vs_scalar_schedule',MODES[1],MODES[2])]}
 row['aa_ratio']=triple.get('calibration_ratio');row['aa_pass']=triple.get('calibration_within_bound')
 if not triple.get('same_calibration'):errors.append(f'calibration mismatch {index}/{fixture}')
 rows.append(row)
cases=[]
for i,inst in enumerate(instances):
 selected=[x for x in rows if x['index']==i];valid=[x for x in selected if 'ratios' in x]
 case=dict(index=i,curve_id=inst['curve_id'],n=inst['field']['degree'],attempted=len(selected),valid=len(valid),expected=24,aa_failures=sum(x['aa_pass'] is False for x in selected),qualification=None,contrasts={})
 if len(valid)==24:
  for name in ['native_vs_incumbent','native_vs_scalar_schedule','scalar_schedule_vs_incumbent']:
   values=[x['ratios'][name] for x in valid];case['contrasts'][name]=dict(median=med(values),bootstrap95=boot(values))
  case['through_cleanup_contrasts']={name:dict(median=med([x['through_cleanup_ratios'][name] for x in valid]),bootstrap95=boot([x['through_cleanup_ratios'][name] for x in valid])) for name in ['native_vs_incumbent','native_vs_scalar_schedule']}
  case['methods']={m:dict(mean_collector_s=statistics.mean(x['methods'][m]['collector_s'] for x in valid),mean_context_plus_computation_s=statistics.mean(x['methods'][m]['context_plus_computation_s'] for x in valid),median_queries=med([x['methods'][m]['queries'] for x in valid]),median_rho_over_ic={k:med([x['methods'][m]['rho_over_ic'][k] for x in valid]) for k in ['rho-plain','rho-negation']},max_rss_kib=max(x['methods'][m]['peak_rss_kib'] or 0 for x in valid)) for m in MODES}
 cases.append(case)
result=dict(status='pass' if not errors else 'failed',errors=errors,qualification=None,standing='unsigned exploratory producer analysis; no signed performance verdict',primary_interval='collector through matrix and owned collector cleanup; independent Python replay separate',cases=cases,rows=rows,aa_failed_rows=[dict(index=x['index'],fixture=x['fixture'],ratio=x['aa_ratio']) for x in rows if x['aa_pass'] is False],capped_arms=sum(x['methods'][m]['exit_code']==124 for x in rows for m in MODES))
(P/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['rows']}))
if errors:raise SystemExit(1)
