#!/usr/bin/env python3
"""Independent read-only audit of the archived GLV Tier-1 paired walltime artifact."""
import argparse,hashlib,json,math,random,statistics,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--results',required=True);p.add_argument('--output',required=True);p.add_argument('--receipts');a=p.parse_args()
zpath=Path(a.archive);digest=hashlib.sha256(zpath.read_bytes()).hexdigest();expected='07d3b18f56b07dcd3826e6932529235791ae7f49b821fa638380b2130d607450';assert digest==expected,(digest,expected)
z=zipfile.ZipFile(zpath); names=z.namelist();assert len(names)==960; assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
summary_paths=sorted(n for n in names if n.endswith('/summary.json'));assert len(summary_paths)==14
published=json.loads(Path(a.results).read_text());out={'schema':'glv-cap-walltime-independent-archive-audit/v1','archive_sha256':digest,'archive_files':len(names),'cells':{},'failures':[]}
for path in summary_paths:
 base=path.removesuffix('summary.json');summary=json.loads(z.read(path));manifest=json.loads(z.read(base+'manifest.json'));case=manifest['cases'][0]['id'];cell=case.removeprefix('glv-').replace('-','_');assert cell in published
 if a.receipts:
  rdir=Path(a.receipts)
  committed_preflight=json.loads((rdir/f'preflight_{cell}.json').read_text())
  archived_preflight=json.loads(z.read(base+'preflight.json'))
  assert committed_preflight['ok'] and archived_preflight['ok']
  for key in ('allocation','architecture','compiler','cpu.max','cpu_model','cpus','execution_cpu','host','host_exclusivity_proved','kernel','memory.max','virtualization'):
   assert committed_preflight['evidence'][key]==archived_preflight['evidence'][key],(cell,key)
  assert json.loads((rdir/f'run-summary_{cell}.json').read_text())['summary']==summary
 pairs=[json.loads(x) for x in z.read(base+'pairs.jsonl').splitlines() if x.strip()];runs=[json.loads(x) for x in z.read(base+'runs.jsonl').splitlines() if x.strip()]
 assert len(pairs)==15 and len(runs)==30,(cell,len(pairs),len(runs))
 assert all(x['status']=='valid' and not x['issues'] for x in pairs)
 assert all(x['status']=='valid' and x['returncode']==0 and not x['timed_out'] and x['fields']['verified']=='1' and x['postflight']['ok'] for x in runs)
 assert len({(x['repeat'],x['variant']) for x in runs})==30
 by={(x['repeat'],x['variant']):x for x in runs}
 ratios=[];opref=set();opcand=set();shas={'reference':set(),'candidate':set()}
 for pair in pairs:
  rep=pair['repeat'];r=by[(rep,'reference')];c=by[(rep,'candidate')]
  assert pair['run_serials']=={'reference':r['serial'],'candidate':c['serial']}
  for key in manifest['pair_fields']:assert r['fields'][key]==c['fields'][key],(cell,rep,key)
  for variant,run in (('reference',r),('candidate',c)):
   assert run['fields']['result']==manifest['cases'][0]['expected_result']
   for key,val in manifest['cases'][0]['expected_fields'].items():assert run['fields'][key]==val,(cell,key)
   shas[variant].add(run['binary_sha256'])
   assert run['online_ms']==float(run['fields']['online_ms'])
  ratio=r['online_ms']/c['online_ms'];assert math.isclose(ratio,pair['speedup'],rel_tol=1e-12,abs_tol=1e-12),(cell,rep)
  ratios.append(ratio);opref.add(int(r['fields']['ops']));opcand.add(int(c['fields']['ops']))
 assert len(opref)==len(opcand)==1
 assert all(len(v)==1 for v in shas.values())
 assert summary['valid_pairs']==15 and summary['status']=='completed' and summary['tier']=='tier1'
 assert summary['binaries_stable'] and summary['artifacts_stable'] and summary['runner_stable'] and not summary['host_exclusivity_proved']
 med=statistics.median(ratios);pub=published[cell]
 assert math.isclose(med,pub['wall_ratio_ref_over_cand'],abs_tol=1e-12,rel_tol=0),(cell,med,pub['wall_ratio_ref_over_cand'])
 assert math.isclose(med,summary['observed_ratio_median'],abs_tol=1e-12,rel_tol=0)
 assert next(iter(opref))==pub['ops_ref'] and next(iter(opcand))==pub['ops_cand']
 op_ratio=next(iter(opref))/next(iter(opcand));assert math.isclose(op_ratio,pub['ops_ratio_ref_over_cand'],abs_tol=1e-12,rel_tol=0)
 assert math.isclose(med/op_ratio,pub['nsop_ratio_ref_over_cand'],abs_tol=1e-12,rel_tol=0)
 if pub['wall_ci95'][0]>1:assert pub['resolved']=='faster' and pub['paired_speedup']==med
 elif pub['wall_ci95'][1]<1:assert pub['resolved']=='slower' and pub['paired_speedup'] is None
 else:assert pub['resolved']=='not resolved' and pub['paired_speedup'] is None
 rng=random.Random('20261107:'+cell);bs=[]
 for _ in range(10000):bs.append(statistics.median(ratios[rng.randrange(15)] for _ in range(15)))
 bs.sort();ci=[bs[250],bs[9750]]
 assert abs(ci[0]-pub['wall_ci95'][0])<0.008 and abs(ci[1]-pub['wall_ci95'][1])<0.008,(cell,ci,pub['wall_ci95'])
 out['cells'][cell]={'case':case,'valid_pairs':len(pairs),'run_rows':len(runs),'median_ratio_ref_over_cand':med,'published_ci95':pub['wall_ci95'],'independent_bootstrap_ci95':ci,'ops_ref':next(iter(opref)),'ops_cand':next(iter(opcand)),'ops_ratio_ref_over_cand':op_ratio,'nsop_ratio_ref_over_cand':med/op_ratio,'resolved':pub['resolved'],'binary_sha256':{k:next(iter(v)) for k,v in shas.items()},'host_exclusivity_proved':False}
assert len(out['cells'])==14
out['committed_summaries_logically_identical']=14 if a.receipts else None
out['committed_preflight_stable_fields_match']=14 if a.receipts else None
out['valid_pairs_total']=sum(x['valid_pairs'] for x in out['cells'].values());out['run_rows_total']=sum(x['run_rows'] for x in out['cells'].values());out['faster_cells']=sum(x['resolved']=='faster' for x in out['cells'].values());out['slower_cells']=sum(x['resolved']=='slower' for x in out['cells'].values());out['not_resolved_cells']=sum(x['resolved']=='not resolved' for x in out['cells'].values())
Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='cells'},indent=2))
