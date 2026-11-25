#!/usr/bin/env python3
"""Audit canonical identities, exact native parameter presence and independent targets."""
import hashlib,json,sys,time
from pathlib import Path
from setup_fresh_common import MODES,ACTUAL,TAGS,FIXTURES
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
sys.path.insert(0,str(ROOT/'experiments/fb-archive'))
from purepy import PyField
from external import _smul
sha=lambda b:hashlib.sha256(b).hexdigest()
digest=lambda v:sha(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
integer=lambda v:int(v,0) if isinstance(v,str) and v.startswith('0x') else int(v)
ids=json.loads((P/'setup-fresh-identities.json').read_text());instances=json.loads((P/'instances.json').read_text());checks=0;candidate_checks=0;new=set();reused=set();wids=set();started=time.monotonic()
for i,inst in enumerate(instances):
 case=ids[str(i)];f,c=inst['field'],inst['curve'];K=PyField(f['degree'],sum(1<<e for e in f['modulus_exponents']));a=integer(c['coefficients'][1]);G=tuple(map(integer,c['generator']))
 for mode in MODES:
  cid=case[mode];candidate=json.loads((ROOT/'experiments/ic-bench/candidates'/f'{cid}.json').read_text())
  assert digest(candidate).startswith(cid.rsplit('h',1)[1]) and candidate['curve']['curve_id']==inst['curve_id']
  if mode in MODES[3:]:
   new.add(cid)
   if mode==MODES[3]:raw=json.loads((P/'cell-smoke-001'/f'{i}-sp.stdout').read_text())
   else:raw=json.loads((P/'setup-cell-smoke-001'/f'{i}-{ACTUAL[mode]}.stdout').read_text())
   params=raw['report']['Ok']['spec']['oracle_params']
   for k,v in candidate['point_decomposition']['params'].items():assert int(params[k])==v,(mode,k)
   assert candidate['implementation']['probe_mode']==ACTUAL[mode]
   assert candidate['implementation']['sources_sha256']==json.loads((P/'setup-build-001/receipt.json').read_text())['source_sha256']
  else:reused.add(cid)
  candidate_checks+=1
 assert set(case['workloads'])=={str(f) for f in FIXTURES}
 for fixture in FIXTURES:
  wid=case['workloads'][str(fixture)];w=json.loads((ROOT/'experiments/ic-bench/workloads'/f'{wid}.json').read_text());wids.add(wid)
  assert digest(w).startswith(wid) and w['fixture']==fixture and w['curve_id']==inst['curve_id'] and w['target_count']==1
  scalar,x,y=w['targets'][0];assert _smul(K,a,G,scalar)==(x,y);checks+=1
assert checks==len(wids)==200 and candidate_checks==40 and len(new)==25 and len(reused)==15
out=P/'local-tmp/setup-identity-check.json';assert not out.exists()
r=dict(status='pass',candidate_checks=candidate_checks,new_candidates=len(new),reused_candidates=len(reused),independent_targets=checks,seconds=time.monotonic()-started,scope='Identity/parameter audit and existing independent Python arithmetic; not native performance',source_sha256={n:sha((ROOT/n).read_bytes()) for n in ['experiments/fb-archive/purepy.py','experiments/fb-archive/external.py',str(Path(__file__).relative_to(ROOT))]})
out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
