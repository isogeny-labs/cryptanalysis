"""Independent Sage verification of every full-panel N41 Macaulay certificate."""
import gzip,hashlib,json,time
from itertools import combinations
from pathlib import Path
from sage.all import GF,PolynomialRing
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'n41_full_audit_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_FULL_N41_SAGE_AUDIT'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
run=json.loads((HERE/'n41_full_result.json').read_text())
assert run['status']=='COMPLETE_FULL_N41_FAMILY_CENSUS' and run['row_count']==7025
assert run['rows_gzip_sha256']==sha(HERE/'n41_full_rows.jsonl.gz')
lines=Path(cfg['sources']['resultant_input']['path']).read_text().splitlines()
valid={}
for line in lines[1:282]:
    tag,code,p,q=line.split();assert tag=='P';valid[int(code)]=(int(p),int(q))
assert len(valid)==281
terms={i:{} for i in range(25)}
for line in lines[282:]:
    words=line.split()
    if words[0]=='C':terms[int(words[1])][int(words[2]),int(words[3])]=int(words[4])
assert all(len(x)==13 for x in terms.values())
R=PolynomialRing(GF(2),'v');v=R.gen()
F=GF(2**41,name='v',modulus=v**41+v**3+1)
enc=lambda x:sum(int(c)<<i for i,c in enumerate(x.polynomial().list()))
dec=lambda x:F.from_integer(x)
seed=dec(112);bits=[0,1,2,3,4,6,7,8,9,10]
qbasis=[]
for bit in bits:
    w=dec(1<<(bit+1));qbasis.append((w*w+seed*w)**(1<<24))
mons=[0]+[1<<i for i in range(10)]+[(1<<i)|(1<<j) for i,j in combinations(range(10),2)]
assert len(mons)==56
start=time.monotonic();checked=0;rejected=0;survivors=[];status='PASS_FULL_N41_CERTIFICATE_AUDIT'
with gzip.open(HERE/'n41_full_rows.jsonl.gz','rt') as stream:
    for line in stream:
        if time.monotonic()-start>=cfg['wall_cap_seconds']:
            status='WALL_CAP_PARTIAL_AUDIT';break
        ti,code,rank,is_reject,cert=json.loads(line)
        assert ti==checked//281 and code==sorted(valid)[checked%281]
        p=dec(valid[code][0]);pp=[F.one(),p]
        for _ in range(3):pp.append(pp[-1]*p)
        byj=[F.zero() for _ in range(5)]
        for (i,j),word in terms[ti].items():byj[j]+=dec(word)*pp[i]
        def evaluate(q):
            qq=[F.one(),q]
            for _ in range(3):qq.append(qq[-1]*q)
            return sum((byj[j]*qq[j] for j in range(5)),F.zero())
        constant=evaluate(F.zero())
        singles=[evaluate(q)+constant for q in qbasis]
        doubles=[evaluate(qbasis[i]+qbasis[j])+singles[i]+singles[j]+constant
                 for i,j in combinations(range(10),2)]
        coeffs=[enc(x) for x in [constant,*singles,*doubles]]
        if is_reject:
            poly={}
            for bit,j in cert:
                assert 0<=bit<41 and -1<=j<10
                m=0 if j<0 else 1<<j
                for source_m,c in zip(mons,coeffs):
                    if c>>bit&1:
                        mm=source_m|m
                        poly[mm]=poly.get(mm,0)^1
            assert {m:b for m,b in poly.items() if b}=={0:1}
            rejected+=1
        else:
            assert cert is None and ti==0 and code==253
            assert evaluate(dec(valid[63][1]))==0
            survivors.append([ti,code])
        checked+=1
assert checked<=7025
if status=='PASS_FULL_N41_CERTIFICATE_AUDIT':
    assert checked==7025 and rejected==7024 and survivors==[[0,253]]
result={'status':status,'rows_checked':checked,'certificates_checked':rejected,
        'unresolved_first_codes':survivors,'wall_seconds':time.monotonic()-start,
        'audit_protocol_sha256':sha(HERE/'n41_full_audit_protocol.json'),
        'auditor_sha256':sha(Path(__file__))}
(HERE/'n41_full_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True),flush=True)
