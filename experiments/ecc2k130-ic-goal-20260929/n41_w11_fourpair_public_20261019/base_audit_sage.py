"""Audit actual cofactor-projected factor bases for W11, W10, W9."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'base_audit_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_BASE_AUDIT'
for v in cfg['sources'].values(): assert sha(v['path'])==v['sha256']
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('base audit wall cap')))
signal.alarm(cfg['wall_cap_seconds'])
start=time.monotonic()
R=PolynomialRing(GF(2),'u');u=R.gen();K=GF(2**41,name='u',modulus=u**41+u**3+1)
E=EllipticCurve(K,[1,0,0,0,1]);O=E(0);r=549756390943
dec=K.from_integer
enc=lambda v:sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
results=[]
for width,name,header in [(11,'join4_input.tsv','W11FOUR 4 1124 1'),
                          (10,'w10/join4_w10_input.tsv','W10FOUR 4 520 1'),
                          (9,'w9/join4_w9_input.tsv','W9FOUR 4 284 1')]:
    lines=(HERE/name).read_text().splitlines();assert lines[0]==header
    states=[list(map(int,line.split()[1:])) for line in lines if line.startswith('S 0 ')]
    codes={row[2] for row in states}
    masks={m for row in states for m in row[4:6]}
    cols={c for row in states for c in row[6:8]}
    raw=[];projected=[]
    for mask in masks:
        a=dec(mask)
        assert a and a.trace()==0 and (1/a).trace()==0
        h=K.zero();t=a
        for _ in range(21):h+=t;t=t**4
        assert h*h+h==a and h
        x=K.one()+1/h
        points=E.lift_x(x,all=True)
        assert len(points)==2
        for p in points:
            q=4*p
            assert q!=O and r*q==O
            raw.append((enc(p[0]),enc(p[1])))
            projected.append((enc(q[0]),enc(q[1])))
    assert len(raw)==len(set(raw))==len(projected)==len(set(projected))==2*len(masks)
    results.append({'width':width,'eligible_codes':len(codes),
                    'distinct_source_masks':len(masks),'usable_base_points':len(projected),
                    'effective_folded_columns':len(cols),
                    'signed_states_per_slot':len(states)})
signal.alarm(0)
res={'status':'PASS_INDEPENDENT_N41_BASE_AUDIT','candidate_id':None,
     'curve_id':cfg['curve_id'],'rows':results,
     'wall_seconds':time.monotonic()-start,
     'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'protocol_sha256':sha(HERE/'base_audit_protocol.json'),
     'script_sha256':sha(__file__)}
(HERE/'base_audit_result.json').write_text(json.dumps(res,sort_keys=True,indent=2)+'\n')
print(json.dumps(res,sort_keys=True))
