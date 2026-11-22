"""Independent carryless-field and Boolean-row rebuild of ordinary rank-seven gate."""
from pathlib import Path
from itertools import combinations
import hashlib,json,resource,signal,time
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'dual_v3_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_GLOBAL_MACAULAY_DUAL_V3'
assert cfg['worker_count']==1
for k,v in cfg['sources'].items():assert sha(v['path'])==v['sha256'],k
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('audit wall cap')))
signal.alarm(cfg['wall_cap_seconds'])
start=time.monotonic()
mod=(1<<41)|(1<<3)|1;mask=(1<<41)-1
def carryless(a,b):
 z=0
 while b:
  if b&1:z^=a
  a<<=1;b>>=1
 return z
def reduce(v):
 while v.bit_length()>41:v^=mod<<(v.bit_length()-42)
 return v
def mul(a,b):return reduce(carryless(a,b))
def sq(a):return mul(a,a)
def rot(a,k):
 for _ in range(k):a=sq(a)
 return a
bits=[0,1,2,3,4,6,7,8,9,10]
def basis(k):return [rot(sq(1<<(i+1))^mul(112,1<<(i+1)),k) for i in bits]
B0=basis(12);B1=basis(24)
source=lambda code,B:__import__('functools').reduce(int.__xor__,(B[i] for i in range(10) if code>>i&1),0)
lines=Path(cfg['sources']['resultant_input']['path']).read_text().splitlines()
assert lines[0]=='FREECODE 25 281 13'
terms={}
for line in lines:
 s=line.split()
 if s[0]=='C' and int(s[1])==1:terms[(int(s[2]),int(s[3]))]=int(s[4])
assert len(terms)==13

def xor_add(dst,m,v):
 dst[m]=dst.get(m,0)^v
 if not dst[m]:del dst[m]
def times(A,B):
 C={}
 for ma,va in A.items():
  for mb,vb in B.items():xor_add(C,ma|mb,mul(va,vb))
 return C
def apowers(B,start):
 A={1<<(start+i):v for i,v in enumerate(B)}
 out=[{0:1},A]
 for _ in range(3):out.append(times(out[-1],A))
 return out
P=apowers(B0,0);Q=apowers(B1,10)
poly={}
for (i,j),c in terms.items():
 term=times(P[i],Q[j])
 for m,v in term.items():xor_add(poly,m,mul(c,v))
assert max(m.bit_count() for m in poly)==4
polysha=hashlib.sha256(json.dumps(sorted(poly.items())).encode()).hexdigest()
prior=json.loads(Path(cfg['sources']['prior_rank7']['path']).read_text())
assert polysha==prior['poly_sha256']
(H/'dual_v3_preflight.json').write_text(json.dumps({'status':'PASS_INDEPENDENT_POLY_PREFLIGHT','poly_sha256':polysha,'poly_monomials':len(poly),'script_sha256':sha(Path(__file__))},sort_keys=True,indent=2)+'\n')
# Directly evaluate the independent 13-term field equation and its Boolean ANF.
for a,b in [(0,0),(1,2),(253,63),(1023,1023),(171,803),(879,4),(550,219)]:
 p=source(a,B0);q=source(b,B1)
 pp=[1,p];qq=[1,q]
 for _ in range(3):pp.append(mul(pp[-1],p));qq.append(mul(qq[-1],q))
 direct=0
 for (i,j),c in terms.items():direct^=mul(c,mul(pp[i],qq[j]))
 word=a|(b<<10);anf=0
 for m,c in poly.items():
  if m&word==m:anf^=c
 assert direct==anf,(a,b)
# Rebuild 41 Boolean equations in a different monomial order.
mons4=[sum(1<<i for i in combo) for d in range(0,5) for combo in combinations(range(20),d)]
idx4={m:i for i,m in enumerate(mons4)}
rows4=[0]*41
for m,c in poly.items():
 while c:
  b=c&-c;rows4[b.bit_length()-1]^=1<<idx4[m];c^=b
mons7=[sum(1<<i for i in combo) for d in range(0,8) for combo in combinations(range(20),d)]
idx7={m:i for i,m in enumerate(mons7)}
mults=[sum(1<<i for i in combo) for d in range(3,-1,-1) for combo in combinations(range(20),d)]
support=[[mons4[i] for i in range(len(mons4)) if row>>i&1] for row in rows4]
constructed=time.monotonic();pivots={};count=0
for t in mults:
 bit={m:1<<idx7[m|t] for m in mons4}
 for terms0 in reversed(support):
  row=0
  for mon in terms0:row^=bit[mon]
  count+=1
  while row:
   pivot=row.bit_length()-1
   if pivot not in pivots:pivots[pivot]=row;break
   row^=pivots[pivot]
  if count%512==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
   raise MemoryError('rss cap')
assert count==55391
unit=1<<idx7[0];remainder=unit
while remainder:
 pivot=remainder.bit_length()-1
 if pivot not in pivots:break
 remainder^=pivots[pivot]
assert len(pivots)==prior['stages'][0]['rank']==55227
assert remainder!=0
# Back-substitute a GF(2) linear functional that annihilates the row span
# and evaluates the constant monomial to one.
assert idx7[0]==0
witness=1
for pivot in sorted(pivots):
 assert pivot>0
 if (pivots[pivot]&witness).bit_count()&1:witness|=1<<pivot
assert witness&1
assert all((row&witness).bit_count()%2==0 for row in pivots.values())
signal.alarm(0)
result={'status':'PASS_GLOBAL_MACAULAY_DUAL_V3','candidate_id':None,
 'curve_id':cfg['curve_id'],'poly_sha256':polysha,'poly_monomials':len(poly),
 'rows_checked':count,'rank':len(pivots),'augmented_unit_rank':len(pivots)+1,
 'dual_witness_hex':hex(witness),'dual_witness_weight':witness.bit_count(),
 'construction_seconds':constructed-start,'rank_seconds':time.monotonic()-constructed,
 'wall_seconds':time.monotonic()-start,'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 'protocol_sha256':sha(H/'dual_v3_protocol.json'),'script_sha256':sha(Path(__file__))}
(H/'dual_v3_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','rows_checked','rank','augmented_unit_rank','wall_seconds','peak_rss_raw')},sort_keys=True))
