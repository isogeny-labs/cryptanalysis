#!/usr/bin/env python3
"""Copy frozen native and separately scoped post-profile values into the record."""
import argparse,json,statistics,subprocess
from pathlib import Path
from setup_fresh_common import MODES
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--record',type=Path,required=True);args=parser.parse_args();record=args.record.resolve()
a=json.loads((P/'analysis-setup-fresh.json').read_text());assert a['status']=='pass' and not json.loads(record.read_text())['metrics']
note='Unsigned exploratory native panel; qualificationnull, invalid for promotion. Primary is context plus pipeline through oracle cleanup; collector has its own owned-cleanup boundary. Prior inputs/startup and later context/report destruction excluded. All A/A failures retained. Pointwise paired bootstrap95 intervals, no broad cold/performance conclusion.'
def metric(name,value,unit,better='neutral',n=None,spread=None,baseline=None,reference=None,scope=note):
 argv=['python3','tools/benchrec.py','metric',str(record),'--name',name,'--value',str(value),'--unit',unit,'--better',better,'--note',scope]
 if n is not None:argv+=['--n',str(n)]
 if spread:argv+=['--spread-low',str(spread[0]),'--spread-high',str(spread[1])]
 if baseline is not None:argv+=['--baseline',str(baseline)]
 if reference is not None:argv+=['--reference',str(reference),'--reference-kind','matched_rho']
 subprocess.run(argv,cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
for c in a['cases']:
 prefix=f"n{c['n']}_";rows=[r for r in a['rows'] if r['index']==c['index']]
 for interval,key in [('primary','through_cleanup_contrasts'),('collector','contrasts'),('table_setup','table_setup_contrasts')]:
  for contrast,value in c[key].items():metric(prefix+interval+'_'+contrast,value['median'],'ratio','neutral' if contrast=='setup_interaction' else 'higher',40,value['bootstrap95'])
 m=c['methods'][MODES[4]];anchor=c['methods'][MODES[1]]
 metric(prefix+'ip_inverse_primary_mean',m['mean_context_plus_computation_s'],'wall_s','lower',40,baseline=anchor['mean_context_plus_computation_s'],reference=statistics.mean(r['references']['rho-negation']['context_plus_compute_s'] for r in rows))
 metric(prefix+'ip_inverse_collector_mean',m['mean_collector_s'],'wall_s','lower',40,baseline=anchor['mean_collector_s'],reference=statistics.mean(r['references']['rho-negation']['compute_s'] for r in rows))
 metric(prefix+'ip_inverse_table_setup_mean',m['mean_table_setup_s'],'wall_s','lower',40,baseline=anchor['mean_table_setup_s'])
 packed=[x['runs'][MODES[4]]['result']['report']['Ok']['decomposition']['setup']['native'] for x in json.loads((P/'timing-setup-001/triples.json').read_text()) if x['index']==c['index']]
 assert len(packed)==40 and all(x['mitm_indexed_prepare_pairs']>=x['mitm_vector_pairs']>0 for x in packed)
 assert len(packed)==40 and all(x['mitm_vector_const_validated_pairs']==x['mitm_vector_const_packed_square_pairs']==x['mitm_vector_const_pairs']==x['mitm_vector_packed_square_pairs']==x['mitm_vector_pairs']>0 for x in packed)
 metric(prefix+'actual_ip_counter_present_tables',sum('mitm_indexed_prepare_pairs' in x for x in packed),'count',n=40,scope='Actual indexed-counter entry presence in IP on each target; not a timing or allocation claim.')
 metric(prefix+'actual_indexed_prepare_pairs',sum(x['mitm_indexed_prepare_pairs'] for x in packed),'count',n=40,scope='Actual source-reported index-driven pairs including scalar fallback lanes; physical-use diagnostic, not native throughput or hardware retirement.')
 metric(prefix+'actual_combined_packed_pairs',sum(x['mitm_vector_const_packed_square_pairs'] for x in packed),'count',n=40,scope='Actual source-reported combined packed-square/constant-reduction pair counters; positive-use diagnostic, not a native throughput or hardware-retirement measurement.')
 for counter in ['elements','padded_lanes']:
  metric(prefix+'actual_ip_inverse_'+counter,sum(r['methods'][MODES[4]]['query_counters']['walk_batch_inverse_vector_'+counter] for r in rows),'count',n=40)
replay=json.loads((P/'independent-arithmetic-setup-fresh.json').read_text())
metric('aa_failed_controls',len(a['aa_failed_rows']),'count',n=200);metric('capped_ic_arms',a['capped_arms'],'count',n=1600)
metric('replayed_target_answers',replay['pipeline_answers']+replay['rho_answers'],'count',n=2000);metric('replayed_aa_answers',replay['aa_answers'],'count',n=400)
metric('replayed_preflight_states',json.loads((P/'independent-states-setup-fresh.json').read_text())['checks'],'count',n=10240)

assert len(json.loads(record.read_text())['metrics'])==180
print(json.dumps({'final_metrics':180}))
