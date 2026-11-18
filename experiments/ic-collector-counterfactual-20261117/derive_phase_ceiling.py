#!/usr/bin/env python3
"""Derived zero-cost phase ceilings; no new measurement or speedup prediction."""
import hashlib,json,statistics
from pathlib import Path
P=Path(__file__).resolve().parent
source=P/'analysis-setup-fresh.json';a=json.loads(source.read_text());assert a['status']=='pass'
out={'schema':'ic-derived-phase-ceiling/v1','standing':'unsigned derived arithmetic; all 40 rows per field retained; no bootstrap or performance prediction','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'indexed-vector16-inverse','reference':'rho-negation context_plus_compute_s','cases':[]}
md=['# Phase ceiling and next optimization admission','','Derived from the completed frozen panel, without rerunning or modifying a workload. These are paired median arithmetic bounds, not measured candidate timings or confidence intervals. All failed A/A controls remain. [pcc:unverified]','','| Field | Table / primary | Collector / primary | Primary / negation rho | Free table: residual / rho | Free collector: residual / rho | Both free: residual / rho |','| --- | --- | --- | --- | --- | --- | --- |']
for c in a['cases']:
 rows=[]
 for r in a['rows']:
  if r['index']!=c['index']:continue
  m=r['methods'][out['method']];p=m['context_plus_computation_s'];t=m['table_setup_s'];k=m['collector_s'];rho=r['references']['rho-negation']['context_plus_compute_s']
  assert min(p,t,k,rho)>0 and p>=t+k
  rows.append(dict(fixture=r['fixture'],table_share=t/p,collector_share=k/p,primary_over_rho=p/rho,free_table_residual_over_rho=(p-t)/rho,free_collector_residual_over_rho=(p-k)/rho,free_both_residual_over_rho=(p-t-k)/rho))
 assert len(rows)==40
 keys=list(rows[0])[1:];v={key:statistics.median(r[key] for r in rows) for key in keys};out['cases'].append(dict(n=c['n'],rows=rows,paired_medians=v));md.append('| N'+str(c['n'])+' | '+' | '.join(f'{v[k]:.4f}' for k in keys)+' |')
md.extend(['','Each residual subtracts only the named recorded phase from that same row primary and divides by its same-target matched negation-rho interval. No cost is amortized across targets; no ratio from another panel is multiplied into this one. Setting a phase to zero is deliberately unattainable and leaves all other recorded costs fixed. It gives an optimistic bound for changing only that phase, not a causal model of cache/allocator changes. [pcc:unverified]','','At N27, removing either table preparation or the entire collector still leaves a large gap. Reservation/gather is rejected as the next performance remedy. The prior static witness dictionary also failed its primary comparison; the reduced Apple ARM wrapper audit already emits native polynomial-multiply instructions. Repeating those leads or adding a C/assembly wrapper does not itself supply a new cost case. [pcc:unverified]','','Next admission must target both dominant phases or reduce relation work algorithmically. Before another timing request: identify an exact operation or data movement eliminated from setup and collection, preserve complete first-witness maps and query order, audit actual compiler output on the relevant native backend, and give a whole-primary cost case. A GPU proposal must include allocation, transfers, table construction and completion of collection; a reused table is a separately named many-target model. No further allocation is launched or requested by this analysis. [pcc:unverified]'])
(P/'phase-ceiling-derived.json').write_text(json.dumps(out,indent=2)+'\n');(P/'NEXT_COST_CASE.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'status':'derived','fields':5,'rows':200,'new_timing_runs':0}))
