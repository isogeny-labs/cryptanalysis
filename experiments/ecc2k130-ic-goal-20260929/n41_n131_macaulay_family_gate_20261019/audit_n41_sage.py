"""Independent Sage replay of N41 resultant ANFs and rejection certificates."""
import hashlib,json,time
from itertools import combinations
from pathlib import Path
from sage.all import GF,PolynomialRing
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'n41_audit_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_INDEPENDENT_N41_AUDIT'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
run=json.loads((HERE/'n41_result.json').read_text())
assert run['status']=='COMPLETE_N41_FAMILY_PANEL' and len(run['rows'])==66
lines=Path(cfg['sources']['resultant_input']['path']).read_text().splitlines()
valid={}
for line in lines[1:282]:
    tag,c,p,q=line.split();assert tag=='P'
    valid[int(c)]=(int(p),int(q))
terms={0:{},1:{}}
for line in lines[282:]:
    words=line.split()
    if words[0]=='C' and int(words[1]) in terms:
        terms[int(words[1])][int(words[2]),int(words[3])]=int(words[4])
R=PolynomialRing(GF(2),'v');v=R.gen()
F=GF(2**41,name='v',modulus=v**41+v**3+1)
def enc(x):return sum(int(c)<<i for i,c in enumerate(x.polynomial().list()))
def dec(x):return F.from_integer(x)
seed=dec(112);bits=[0,1,2,3,4,6,7,8,9,10]
qbasis=[]
for bit in bits:
    w=dec(1<<(bit+1));qbasis.append((w*w+seed*w)**(1<<24))
for code,(_,q) in valid.items():
    actual=sum((qbasis[j] for j in range(10) if code>>j&1),F.zero())
    assert enc(actual)==q
mons=[0]+[1<<i for i in range(10)]+[(1<<i)|(1<<j) for i,j in combinations(range(10),2)]
assert len(mons)==56
start=time.monotonic();checked=0;rejected=0;positive=0
for row in run['rows']:
    if time.monotonic()-start>cfg['wall_cap_seconds']:
        raise TimeoutError('N41 independent audit wall cap')
    ti=row['target_index'];p=dec(row['p_product']);tt=terms[ti]
    pp=[F.one(),p]
    for _ in range(3):pp.append(pp[-1]*p)
    byj=[F.zero() for _ in range(5)]
    for (i,j),word in tt.items():byj[j]+=dec(word)*pp[i]
    def evaluate(q):
        qq=[F.one(),q]
        for _ in range(3):qq.append(qq[-1]*q)
        return sum((byj[j]*qq[j] for j in range(5)),F.zero())
    constant=evaluate(F.zero())
    single=[evaluate(q)+constant for q in qbasis]
    doubles=[evaluate(qbasis[i]+qbasis[j])+single[i]+single[j]+constant
             for i,j in combinations(range(10),2)]
    coeffs=[enc(x) for x in [constant,*single,*doubles]]
    for qcode in (0,1,3,63,253,1023):
        q=sum((qbasis[j] for j in range(10) if qcode>>j&1),F.zero())
        expanded=0
        for mask,c in zip(mons,coeffs):
            if qcode&mask==mask:expanded^=c
        assert expanded==enc(evaluate(q))
    valid_hits=[]
    for qcode in valid:
        candidate=0
        for mask,c in zip(mons,coeffs):
            if qcode&mask==mask:candidate^=c
        if candidate==0:valid_hits.append(qcode)
    assert sorted(valid_hits)==row['valid_q_hits']
    if row['reject']:
        poly={}
        for bit,j in row['certificate_rows']:
            assert 0<=bit<41 and -1<=j<10
            multiplier=0 if j<0 else 1<<j
            for mask,c in zip(mons,coeffs):
                if c>>bit&1:
                    mm=mask|multiplier
                    poly[mm]=poly.get(mm,0)^1
        assert {m:b for m,b in poly.items() if b}=={0:1}
        assert not valid_hits
        rejected+=1
    else:
        assert row['certificate_rows'] is None
        if ti==0 and row['p_code']==253:
            assert 63 in valid_hits and evaluate(dec(valid[63][1]))==0
            positive+=1
    checked+=1
assert checked==66 and rejected==65 and positive==1
result={'status':'PASS_INDEPENDENT_N41_MACAULAY_PANEL','rows_checked':checked,
        'rejected_certificates_checked':rejected,'positive_families_preserved':positive,
        'wall_seconds':time.monotonic()-start,'audit_protocol_sha256':sha(HERE/'n41_audit_protocol.json'),
        'auditor_sha256':sha(Path(__file__))}
(HERE/'n41_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True),flush=True)
