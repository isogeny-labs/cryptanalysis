"""Replay dual parity certificate using the original symbolic ANF construction."""
from pathlib import Path
from itertools import combinations
import hashlib,json,sys,time
ROOT=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/n41_n131_macaulay_family_gate_20261019')
sys.path.insert(0,str(ROOT))
from macaulay import Field,source_basis,source_value,evaluate_resultant
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'dual_verify_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_DUAL_CERTIFICATE_REPLAY'
for k,v in cfg['sources'].items():assert sha(v['path'])==v['sha256'],k
start=time.monotonic()
dual=json.loads(Path(cfg['sources']['dual_result']['path']).read_text())
witness=int(dual['dual_witness_hex'],16)
assert witness&1 and witness.bit_count()==dual['dual_witness_weight']
f=Field(41,(1<<3)|1)
lines=Path(cfg['sources']['resultant_input']['path']).read_text().splitlines()
terms={}
for line in lines:
 s=line.split()
 if s[0]=='C' and int(s[1])==1:terms[(int(s[2]),int(s[3]))]=int(s[4])
bits=[0,1,2,3,4,6,7,8,9,10]
pbasis=source_basis(f,112,bits,12);qbasis=source_basis(f,112,bits,24)
def mul(A,B):
 out={}
 for ma,ca in A.items():
  for mb,cb in B.items():
   m=ma|mb;out[m]=out.get(m,0)^f.mul(ca,cb)
 return {m:c for m,c in out.items() if c}
def powers(basis,offset):
 p1={1<<(offset+i):v for i,v in enumerate(basis)}
 p2={1<<(offset+i):f.square(v) for i,v in enumerate(basis)}
 p3=mul(p1,p2)
 p4={1<<(offset+i):f.square(f.square(v)) for i,v in enumerate(basis)}
 return [{0:1},p1,p2,p3,p4]
P=powers(pbasis,0);Q=powers(qbasis,10);poly={}
for (i,j),c in terms.items():
 for ma,ca in P[i].items():
  for mb,cb in Q[j].items():
   m=ma|mb;poly[m]=poly.get(m,0)^f.mul(c,f.mul(ca,cb))
poly={m:c for m,c in poly.items() if c}
assert hashlib.sha256(json.dumps(sorted(poly.items())).encode()).hexdigest()==dual['poly_sha256']
mon4=[0]+[sum(1<<i for i in c) for d in range(1,5) for c in combinations(range(20),d)]
idx4={m:i for i,m in enumerate(mon4)}
eq=[0]*41
for m,c in poly.items():
 while c:
  bit=c&-c;eq[bit.bit_length()-1]^=1<<idx4[m];c^=bit
mon7=[0]+[sum(1<<i for i in c) for d in range(1,8) for c in combinations(range(20),d)]
idx7={m:i for i,m in enumerate(mon7)}
mults=[0]+[sum(1<<i for i in c) for d in range(1,4) for c in combinations(range(20),d)]
assert len(mon7)==137980 and len(mults)==1351
checked=0
for t in mults:
 mask=0
 for m in mon4:
  if witness>>idx7[m|t]&1:mask|=1<<idx4[m]
 for row in eq:
  assert (row&mask).bit_count()%2==0,(t,checked)
  checked+=1
assert checked==55391
assert witness>>idx7[0]&1
result={'status':'PASS_GLOBAL_MACAULAY_DUAL_REPLAY','candidate_id':None,
 'curve_id':cfg['curve_id'],'rows_checked':checked,'unit_value':1,'row_values_all_zero':True,
 'poly_sha256':dual['poly_sha256'],'dual_witness_weight':witness.bit_count(),
 'wall_seconds':time.monotonic()-start,'protocol_sha256':sha(H/'dual_verify_protocol.json'),
 'script_sha256':sha(Path(__file__))}
(H/'dual_verify_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
