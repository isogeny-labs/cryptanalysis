#!/usr/bin/env python3
"""Replay every completed profile answer with existing independent arithmetic."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args();assert args.run_id.replace('-','').isalnum()
sys.path.insert(0,str(ROOT/'experiments/fb-archive'));from purepy import PyField;from external import _smul
rows=json.loads((P/args.run_id/'results.json').read_text());inst=json.loads((P/'instances.json').read_text())[4]
integer=lambda v:int(v,0) if isinstance(v,str) and v.startswith('0x') else int(v)
f,c=inst['field'],inst['curve'];K=PyField(f['degree'],sum(1<<e for e in f['modulus_exponents']));a=integer(c['coefficients'][1]);G=tuple(map(integer,c['generator']));checks=[]
for row in rows:
 raw=row['result'];r=raw['solver'] if row['mode'].startswith('rho-') else raw['report']['Ok']
 assert r['verified'] and r['recovered']==raw['planted']
 assert _smul(K,a,G,r['recovered'])==tuple(raw['target'])
 checks.append(dict(label=row['label'],mode=row['mode'],scalar=r['recovered'],target=raw['target']))
sources=['experiments/fb-archive/purepy.py','experiments/fb-archive/external.py',str(Path(__file__).relative_to(ROOT))]
result=dict(status='pass',checks=len(checks),rows=checks,standing='unsigned producer invocation of existing independent arithmetic',source_sha256={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources})
(P/f'replay-{args.run_id}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['rows','source_sha256']}))
