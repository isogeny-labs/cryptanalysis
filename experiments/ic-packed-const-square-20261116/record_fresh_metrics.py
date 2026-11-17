#!/usr/bin/env python3
"""Copy frozen native and separately scoped post-profile values into the record."""
import argparse,json,statistics,subprocess
from pathlib import Path
from fresh_common import MODES
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--record',type=Path,required=True);args=parser.parse_args();record=args.record.resolve()
a=json.loads((P/'analysis-fresh.json').read_text());assert a['status']=='pass' and not json.loads(record.read_text())['metrics']
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
  for contrast,value in c[key].items():metric(prefix+interval+'_'+contrast,value['median'],'ratio','higher',30,value['bootstrap95'])
 m=c['methods'][MODES[4]];anchor=c['methods'][MODES[2]]
 metric(prefix+'patched_inverse_primary_mean',m['mean_context_plus_computation_s'],'wall_s','lower',30,baseline=anchor['mean_context_plus_computation_s'],reference=statistics.mean(r['references']['rho-negation']['context_plus_compute_s'] for r in rows))
 metric(prefix+'patched_inverse_collector_mean',m['mean_collector_s'],'wall_s','lower',30,baseline=anchor['mean_collector_s'],reference=statistics.mean(r['references']['rho-negation']['compute_s'] for r in rows))
 metric(prefix+'patched_inverse_table_setup_mean',m['mean_table_setup_s'],'wall_s','lower',30,baseline=anchor['mean_table_setup_s'])
 packed=[x['runs'][MODES[4]]['result']['report']['Ok']['decomposition']['setup']['native'] for x in json.loads((P/'timing-optimized-001/triples.json').read_text()) if x['index']==c['index']]
 assert len(packed)==30 and all(x['mitm_vector_const_packed_square_pairs']==x['mitm_vector_const_pairs']==x['mitm_vector_packed_square_pairs']==x['mitm_vector_pairs']>0 for x in packed)
 metric(prefix+'actual_combined_packed_pairs',sum(x['mitm_vector_const_packed_square_pairs'] for x in packed),'count',n=30,scope='Actual source-reported combined packed-square/constant-reduction pair counters; positive-use diagnostic, not a native throughput or hardware-retirement measurement.')
 for counter in ['elements','padded_lanes']:
  metric(prefix+'actual_patched_inverse_'+counter,sum(r['methods'][MODES[4]]['query_counters']['walk_batch_inverse_vector_'+counter] for r in rows),'count',n=30)
replay=json.loads((P/'independent-arithmetic-fresh.json').read_text())
metric('aa_failed_controls',len(a['aa_failed_rows']),'count',n=150);metric('capped_ic_arms',a['capped_arms'],'count',n=750)
metric('replayed_target_answers',replay['pipeline_answers']+replay['rho_answers'],'count',n=1050);metric('replayed_aa_answers',replay['aa_answers'],'count',n=300)
metric('replayed_preflight_states',json.loads((P/'independent-states-fresh.json').read_text())['checks'],'count',n=7680)
post=json.loads((P/'analysis-post-profile.json').read_text())
scope='Separate pre-timing preparation fixed-development-point Callgrind whole-guest Ir; not native timing, hardware retirement or collector-only cost. One trace per method; exact prior tool/calibration/point/work pins. Unsigned qualificationnull.'
for r in post['rows']:
 metric('post_'+r['method']+'_whole_guest_ir',r['ir'],'ir','lower',1,scope=scope)
 metric('post_'+r['method']+'_generic_dispatch_exclusive_ir',r['generic_dispatch_exclusive_ir'],'ir','lower',1,scope=scope)
 metric('post_'+r['method']+'_walker_wide_remainder_calls',sum(e['calls'] for e in r['walker_wide_remainder_edges']),'count','lower',1,scope=scope)
pr=json.loads((P/'independent-replay-post-profile.json').read_text());metric('post_replayed_answers',pr['answer_checks'],'count',n=2,scope=scope);metric('post_replayed_states',pr['state_checks'],'count',n=512,scope=scope)
print(json.dumps({'metrics':len(json.loads(record.read_text())['metrics'])}))
