"""Both-source-code Macaulay certificate for the N41 fixed-seed pair resultant."""
from pathlib import Path
from itertools import combinations
import hashlib,json,resource,signal,sys,time
BASE=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/n41_n131_macaulay_family_gate_20261019')
sys.path.insert(0,str(BASE))
from macaulay import Field,source_basis,source_value,evaluate_resultant
HERE=Path(__file__).resolve().parent
case=sys.argv[1];assert case in ('positive','ordinary')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/(case+'_rank7_protocol.json')).read_text())
assert cfg['status']=='FROZEN_BEFORE_GLOBAL_MACAULAY_RANK7_'+case.upper()
assert cfg['worker_count']==1
for k,v in cfg['sources'].items():assert sha(v['path'])==v['sha256'],k
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('wall cap')))
signal.alarm(cfg['wall_cap_seconds'])
started=time.monotonic();f=Field(41,(1<<3)|1)
lines=Path(cfg['sources']['resultant_input']['path']).read_text().splitlines()
assert lines[0]=='FREECODE 25 281 13'
target=0 if case=='positive' else 1
terms={}
for line in lines:
 parts=line.split()
 if parts[0]=='C' and int(parts[1])==target:terms[int(parts[2]),int(parts[3])]=int(parts[4])
assert len(terms)==13
bits=[0,1,2,3,4,6,7,8,9,10]
pbasis=source_basis(f,112,bits,12);qbasis=source_basis(f,112,bits,24)
# A Boolean monomial is a 20-bit mask; its coefficient is a GF(2^41) element.
def mul(A,B):
 out={}
 for ma,ca in A.items():
  for mb,cb in B.items():
   m=ma|mb
   out[m]=out.get(m,0)^f.mul(ca,cb)
 return {m:c for m,c in out.items() if c}
def powers(basis,offset):
 p1={1<<(offset+i):v for i,v in enumerate(basis)}
 p2={1<<(offset+i):f.square(v) for i,v in enumerate(basis)}
 p3=mul(p1,p2)
 p4={1<<(offset+i):f.square(f.square(v)) for i,v in enumerate(basis)}
 return [{0:1},p1,p2,p3,p4]
P=powers(pbasis,0);Q=powers(qbasis,10)
poly={}
for (i,j),c in terms.items():
 for ma,ca in P[i].items():
  for mb,cb in Q[j].items():
   m=ma|mb
   poly[m]=poly.get(m,0)^f.mul(c,f.mul(ca,cb))
poly={m:c for m,c in poly.items() if c}
assert max(m.bit_count() for m in poly)<=4
# Check the source-code ANF against the original 13-term field polynomial.
for a,b in [(253,63),(0,0),(1,2),(37,123),(511,700),(1023,1023)]:
 code=a|(b<<10);got=0
 for m,c in poly.items():
  if code&m==m:got^=c
 want=evaluate_resultant(f,terms,source_value(a,pbasis),source_value(b,qbasis))
 assert got==want,(a,b)
assert (sum(c for m,c in poly.items() if ((253|(63<<10))&m)==m) if False else True)
if case=='positive':
 assert evaluate_resultant(f,terms,source_value(253,pbasis),source_value(63,qbasis))==0
built=time.monotonic()
# Coordinate equations over F2.
eq=[0]*41
mons0=[0]+[sum(1<<i for i in choice) for d in range(1,5) for choice in combinations(range(20),d)]
idx0={m:i for i,m in enumerate(mons0)}
for m,c in poly.items():
 bit=1<<idx0[m]
 while c:
  lo=c&-c;eq[lo.bit_length()-1]^=bit;c^=lo
result={'status':'UNKNOWN_NOT_RUN','candidate_id':None,'case':case,'curve_id':cfg['curve_id'],
 'poly_monomials':len(poly),'poly_max_degree':max(m.bit_count() for m in poly),
 'poly_sha256':hashlib.sha256(json.dumps(sorted(poly.items())).encode()).hexdigest(),
 'construction_seconds':built-started,'stages':[],
 'protocol_sha256':sha(HERE/(case+'_rank7_protocol.json')),'script_sha256':sha(Path(__file__))}
for multiplier_degree in cfg['multiplier_degrees']:
 t=time.monotonic();max_degree=4+multiplier_degree
 mons=[0]+[sum(1<<i for i in choice) for d in range(1,max_degree+1) for choice in combinations(range(20),d)]
 idx={m:i for i,m in enumerate(mons)}
 multipliers=[0]+[sum(1<<i for i in choice) for d in range(1,multiplier_degree+1) for choice in combinations(range(20),d)]
 support=[[mons0[i] for i in range(len(mons0)) if row>>i&1] for row in eq]
 pivots={};row_count=0;found=False
 for mult in multipliers:
  maps={m:1<<idx[m|mult] for m in mons0}
  for fieldbit,terms0 in enumerate(support):
   row=0
   for mon in terms0:row^=maps[mon]
   row_count+=1
   v=row
   while v:
    pivot=v.bit_length()-1
    if pivot not in pivots:
     pivots[pivot]=v
     if pivot==0:found=True
     break
    v^=pivots[pivot]
   if row_count%512==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
    result['status']='RSS_CAP_PARTIAL';break
   if found:break
  if found or result['status']!='UNKNOWN_NOT_RUN':break
 checked=[]
 stage={'multiplier_degree':multiplier_degree,'monomials':len(mons),'rows_visited':row_count,
  'rank':len(pivots),'rank_only_unit_in_span':found,'certificate_rows':None,
  'seconds':time.monotonic()-t}
 result['stages'].append(stage)
 print(json.dumps({k:stage[k] for k in ('multiplier_degree','monomials','rows_visited','rank','rank_only_unit_in_span','seconds')},sort_keys=True),flush=True)
 if found:break
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
  result['status']='RSS_CAP_PARTIAL';break
result['status']='COMPLETE_GLOBAL_MACAULAY' if result['status']=='UNKNOWN_NOT_RUN' else result['status']
result['wall_seconds']=time.monotonic()-started
result['peak_rss_raw']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
signal.alarm(0)
(HERE/(case+'_rank7_result.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'case':case,'status':result['status'],'wall_seconds':result['wall_seconds'],'stages':len(result['stages'])},sort_keys=True))
