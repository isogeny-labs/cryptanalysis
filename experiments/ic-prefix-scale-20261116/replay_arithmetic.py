#!/usr/bin/env python3
"""Replay returned scalars with the existing independent Python group code."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/fb-archive'))
from purepy import PyField
from external import _smul
parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='timing-001');parser.add_argument('--stem',default='independent-arithmetic-timing001');args=parser.parse_args()
assert args.run_id.replace('-','').isalnum() and args.stem.replace('-','').isalnum()
instances=json.loads((HERE/'instances.json').read_text())
pairs=json.loads((HERE/args.run_id/'triples.json').read_text());refs=json.loads((HERE/args.run_id/'references.json').read_text())
integer=lambda v:int(v,0) if isinstance(v,str) and v.startswith('0x') else int(v)
checks=[];pipeline=0;rho=0
for index,entry in enumerate(instances):
 f,c=entry['field'],entry['curve'];K=PyField(f['degree'],sum(1<<e for e in f['modulus_exponents']));a=integer(c['coefficients'][1]);G=tuple(map(integer,c['generator']))
 for pair in [p for p in pairs if p['index']==index]:
  for variant in ['mitm-native','mitm-scalar','mitm-prefix','mitm-auto']:
   raw=pair['runs'][variant].get('result');report=(raw or {}).get('report',{}).get('Ok')
   if not report or not report['verified']:continue
   d=report['recovered'];Q=tuple(raw['target'])
   assert _smul(K,a,G,d)==Q
   pipeline+=1;checks.append({'index':index,'fixture':pair['fixture'],'method':'registered-scaling-panel','variant':variant,'scalar':d,'target':list(Q)})
 for ref in [r for r in refs if r['index']==index]:
  raw=ref.get('result')
  if not raw:continue
  Q=tuple(raw['target'])
  for kind in ['plain','matched']:
   if not raw[kind]['verified']:continue
   d=raw[kind]['recovered'];assert _smul(K,a,G,d)==Q
   rho+=1;checks.append({'index':index,'fixture':ref['fixture'],'method':'rho-'+kind,'scalar':d,'target':list(Q)})
sources=['experiments/fb-archive/purepy.py','experiments/fb-archive/external.py',str(Path(__file__).relative_to(ROOT))]
result={'schema':'ic-affine-existing-python-arithmetic-replay/v1','status':'pass','checks':len(checks),'pipeline_answers':pipeline,'rho_answers':rho,
        'implementation':'experiments/fb-archive/purepy.py PyField and external.py _smul',
        'standing':'unsigned producer invocation of an existing independent arithmetic implementation','rows':checks,
        'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
(HERE/(args.stem+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','source_sha256']}))
