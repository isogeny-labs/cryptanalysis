#!/usr/bin/env python3
"""Independent existing Python arithmetic checks of every exported walk state."""
import argparse,hashlib,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/fb-archive'))
from purepy import PyField
from external import _smul
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
started=time.monotonic();cpu=time.process_time();checks=[]
integer=lambda v:int(v,0) if isinstance(v,str) and v.startswith('0x') else int(v)
for index,inst in enumerate(json.loads((HERE/'instances.json').read_text())):
 path=args.directory/f'walk-smoke-{index}.json';raw=json.loads(path.read_text());field=inst['field'];c=inst['curve'];r=integer(c['subgroup_order'])
 K=PyField(field['degree'],sum(1<<e for e in field['modulus_exponents']));a=integer(c['coefficients'][1]);G=tuple(map(integer,c['generator']))
 assert raw['curve_id']==inst['curve_id'] and raw['checks']==512 and len(raw['frames'])==512
 assert _smul(K,a,G,raw['planted'])==tuple(raw['target'])
 for frame in raw['frames']:
  expected=_smul(K,a,G,(frame['a']+frame['b']*raw['planted'])%r)
  assert expected==(None if frame['infinity'] else (frame['x'],frame['y']))
 checks.append(dict(index=index,states=len(raw['frames']),input_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
result=dict(status='pass',checks=sum(x['states'] for x in checks),rows=checks,elapsed_s=time.monotonic()-started,cpu_s=time.process_time()-cpu,standing='unsigned producer invocation of existing independent Python arithmetic',source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['experiments/fb-archive/purepy.py','experiments/fb-archive/external.py']})
args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
