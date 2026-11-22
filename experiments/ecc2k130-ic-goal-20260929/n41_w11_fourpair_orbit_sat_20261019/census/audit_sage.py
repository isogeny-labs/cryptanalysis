"""Independently rebuild every exact W11 four-pair target-orbit witness."""
import collections
import hashlib
import json
import resource
import signal
import time
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'audit_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_W11_ORBIT_CENSUS_AUDIT'
for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('audit wall cap')))
signal.alarm(cfg['wall_cap_seconds'])
begin=time.monotonic()
query=json.loads(Path(cfg['sources']['query_result']['path']).read_text())
assert query['status']=='COMPLETE_CENSUS'
lines=Path(cfg['sources']['query_stdout']['path']).read_text().splitlines()
hits=[x.split() for x in lines if x.startswith('HIT ')]
assert len(hits)==query['hit_lines']
R=PolynomialRing(GF(2),'u');u=R.gen();K=GF(2**41,name='u',modulus=u**41+u**3+1)
E=EllipticCurve(K,[1,0,0,0,1]);O=E(0);order=549756390943
dec=K.from_integer
enc=lambda v:sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
def halftrace(v):
    total=K.zero();t=v
    for _ in range(21):total+=t;t=t**4
    assert total*total+total==v
    return total
def source_points(a):
    h=halftrace(a);assert h
    return E.lift_x(K.one()+1/h,all=True)
def column(a):
    x=K.one()+1/halftrace(a)
    return min(enc(x**(1<<j)) for j in range(41))
table=Path(cfg['sources']['join_input']['path']).read_text().splitlines()
assert table[0]=='W11FOUR 4 1124 1'
target=table[1].split();assert target[:2]==['T','0']
Q0=E(dec(int(target[2])),dec(int(target[3])))
states={}
for line in table[2:]:
    p=line.split()
    if p and p[0]=='S':states[(int(p[1]),int(p[2]))]=list(map(int,p[3:]))
assert len(states)==4*1124
bits=[0,1,2,3,4,6,7,8,9,10]
rotations=[0,12,24,36]
per_orientation=collections.Counter();witnesses=[]
for line in hits:
    orientation=int(line[1]);ids=list(map(int,line[2:6]))
    assert 0<=orientation<41
    Qk=E(Q0[0]**(1<<orientation),Q0[1]**(1<<orientation))
    assert [enc(Qk[0]),enc(Qk[1])]==list(map(int,line[9:11]))
    total=O;folded=[];codes=[]
    for slot,sid in enumerate(ids):
        code,branch,ma,mb,ca,cb,x,y=states[(slot,sid)]
        a=sum((dec(1<<(i+1)) for j,i in enumerate(bits) if code>>j&1),K.zero())
        b=a+dec(112)
        assert a and b and enc(a)==ma and enc(b)==mb
        assert a.trace()==0 and (1/a).trace()==0 and (1/b).trace()==0
        assert column(a)==ca and column(b)==cb
        options=[]
        for ia,pa in enumerate(source_points(a)):
            for ib,pb in enumerate(source_points(b)):
                S=pa+pb
                if S==O:continue
                rotated=E(S[0]**(1<<rotations[slot]),S[1]**(1<<rotations[slot]))
                if rotated==E(dec(x),dec(y)):
                    options.append((ia,ib,pa,pb))
        assert len(options)==1 and branch==2*options[0][0]+options[0][1]
        total+=E(dec(x),dec(y));folded.extend((ca,cb));codes.append(code)
    assert len(set(folded))==8 and total==Qk
    back=E(total[0]**(1<<((41-orientation)%41)),
           total[1]**(1<<((41-orientation)%41)))
    assert back==Q0 and 4*back!=O and order*(4*back)==O
    per_orientation[orientation]+=1
    witnesses.append({'orientation':orientation,'state_ids':ids,'source_codes':codes,
                      'folded_columns':folded})
assert sum(per_orientation.values())==len(hits)
assert query['orientation_done_lines']==41
signal.alarm(0)
result={'status':'PASS_INDEPENDENT_N41_W11_ORBIT_CENSUS','candidate_id':None,
        'curve_id':cfg['curve_id'],'target':list(map(int,target[2:])),
        'hit_count':len(hits),'orientation_counts':dict(sorted(per_orientation.items())),
        'witnesses':witnesses,'wall_seconds':time.monotonic()-begin,
        'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'audit_protocol.json'),'script_sha256':sha(__file__)}
(HERE/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'hit_count':len(hits),
                  'orientations_with_hits':len(per_orientation)},sort_keys=True))
