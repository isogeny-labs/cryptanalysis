#!/usr/bin/env python3
"""Compare packed extraction and proposed folding with existing Python arithmetic."""
import hashlib,json,random,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
sys.path.insert(0,str(ROOT/'experiments/fb-archive'))
from purepy import PyField

def clmul(a,b):
 out=0
 while b:
  if b&1:out^=a
  a<<=1;b>>=1
 return out

def fold(raw,n,tail):
 mask=(1<<n)-1;h=raw>>n;f=clmul(h,tail)
 return ((raw^f)&mask)^clmul(f>>n,tail)

started=time.monotonic();rng=random.Random(0xC0575A20261116);rows=[]
for n,tail in [(15,3),(18,9),(21,5),(24,27),(27,39)]:
 K=PyField(n,(1<<n)|tail);mask=(1<<n)-1;assert 2*(tail.bit_length()-1)-2<n
 squares=0;products=0;packed=0
 # Exhaustive smallest admitted field, then fixed edge and random four-lane vectors.
 if n==15:
  for x in range(1<<n):
   assert fold(clmul(x,x),n,tail)==K.mul(x,x);squares+=1
 edge=[0,1,mask,1<<(n-1)]
 for values in [edge,list(reversed(edge)),*[[rng.getrandbits(n) for _ in range(4)] for _ in range(10000)]]:
  for a,b in zip(values[::2],values[1::2]):
   raw=clmul(a|(b<<32),a|(b<<32));lo=raw&((1<<64)-1);hi=raw>>64
   assert lo==clmul(a,a) and hi==clmul(b,b)
   assert fold(lo,n,tail)==K.mul(a,a) and fold(hi,n,tail)==K.mul(b,b);packed+=2
  for a,b in zip(values,values[1:]+values[:1]):
   assert fold(clmul(a,b),n,tail)==K.mul(a,b);products+=1
 rows.append(dict(n=n,tail=tail,exhaustive_squares=squares,packed_lane_squares=packed,products=products))
out=dict(status='pass',standing='unsigned arithmetic experiment; no native performance claim',rows=rows,elapsed_s=time.monotonic()-started,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['experiments/fb-archive/purepy.py']},checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(P/'arithmetic-check.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
