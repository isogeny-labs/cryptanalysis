#!/usr/bin/env python3
"""Record guest-Ir attribution only, with no native timing interpretation."""
import json, statistics, subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
a=json.loads((P/'analysis-profile-001.json').read_text());record=ROOT/'benchmarks/records/20261117T0128Z-ic-inverse-regression-profile-001.json'
assert not json.loads(record.read_text())['metrics']
med={m:statistics.median(v) for m,v in a['totals'].items()}
note='Whole-guest Callgrind Ir on one fixed development point; not native wall, hardware retirement or collector-only cost. Unsigned exploratory qualificationnull. Two IC traces, one trace per rho variant; repeated extrema are not a native confidence interval.'
def metric(name,value,unit,n=1,baseline=None,reference=None,spread=None,better='neutral'):
 argv=['python3','tools/benchrec.py','metric',str(record),'--name',name,'--value',str(value),'--unit',unit,'--n',str(n),'--better',better,'--note',note]
 if baseline is not None:argv+=['--baseline',str(baseline)]
 if reference is not None:argv+=['--reference',str(reference),'--reference-kind','matched_rho']
 if spread:argv+=['--spread-low',str(spread[0]),'--spread-high',str(spread[1])]
 subprocess.run(argv,cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
for m in ['anchor','current','inverse']:metric(m+'_whole_guest_ir',med[m],'ir',2,med['anchor'],med['rho-negation'],[min(a['totals'][m]),max(a['totals'][m])],better='lower')
for m in ['rho-plain','rho-negation']:metric(m+'_whole_guest_ir',med[m],'ir',better='lower')
for name,x,y in [('anchor_over_current_ir','anchor','current'),('current_over_inverse_ir','current','inverse'),('anchor_over_inverse_ir','anchor','inverse')]:metric(name,med[x]/med[y],'ratio',2,better='higher')
metric('current_general_dispatch_calls',55163,'count',2,baseline=0)
metric('current_general_dispatch_exclusive_ir',1933760,'ir',2,baseline=0)
metric('ordinary_pairwise_extra_inclusive_ir',34511,'ir',2)
metric('replayed_answers',8,'count',8);metric('replayed_states',1024,'count',1024)
print(json.dumps({'metrics':len(json.loads(record.read_text())['metrics'])}))
