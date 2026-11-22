"""Exact target-conditioned 3+2 lookup on sign-quotiented partial sums."""
import hashlib, itertools, json, resource, sys, time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing
H=Path(__file__).resolve().parent
case=sys.argv[1]
assert case in ('n41','n131')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/(case+'_protocol.json')).read_text())
assert cfg['status']=='FROZEN_BEFORE_PREFIX_SUFFIX_X_'+case.upper()
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
start=time.monotonic();R=PolynomialRing(GF(2),'u');u=R.gen();n=41 if case=='n41' else 131
mod=u**41+u**3+1 if n==41 else u**131+u**13+u**2+u+1
F=GF(2**n,name='u',modulus=mod);E=EllipticCurve(F,[1,0,0,0,1]);dec=F.from_integer;O=E(0)
enc=lambda v:sum(int(bit)<<i for i,bit in enumerate(v.polynomial().list()))
boxes=[]
if case=='n41':
    panel=json.loads(Path(cfg['sources']['panel']['path']).read_text());states=[{} for _ in range(5)]
    for line in Path(cfg['sources']['join_input']['path']).read_text().splitlines()[2:]:
        c=line.split()
        if c[0]=='S':
            slot,sid,code,branch,a,b,ca,cb,x,y=map(int,c[1:]);states[slot][sid]=E(dec(x),dec(y))
    for b in panel['boxes']:
        choices=[[states[j][sid] for pair in b['root_choices'][j] for sid in pair] for j in range(5)]
        boxes.append((b['kind'],choices,E(*(dec(v) for v in panel['target_point']))))
else:
    panel=json.loads(Path(cfg['sources']['panel']['path']).read_text())
    for b in panel['boxes']:
        choices=[[E(*(dec(v) for v in xy)) for choice in b['choices'][j]
                  for xy in choice['signed_points']] for j in range(5)]
        boxes.append((b['kind'],choices,E(*(dec(v) for v in b['target_point']))))
rows=[];status='COMPLETE_PREFIX_SUFFIX_X'
for index,(kind,choices,target) in enumerate(boxes):
    if time.monotonic()-start>cfg['wall_cap_seconds']:status='WALL_CAP_PARTIAL';break
    assert all(len(slot)==4 for slot in choices)
    t=time.monotonic();prefix={};suffix={}
    for ids in itertools.product(range(4),repeat=3):
        P=sum((choices[j][ids[j]] for j in range(3)),O);x=None if P==O else enc(P[0])
        prefix.setdefault(x,[]).append((ids,P))
    for ids in itertools.product(range(4),repeat=2):
        P=choices[3][ids[0]]+choices[4][ids[1]];x=None if P==O else enc(P[0])
        suffix.setdefault(x,[]).append((ids,P))
    prep=time.monotonic()-t;t=time.monotonic();hits=set();checks=queries=0
    for x,bucket in prefix.items():
        P=bucket[0][1];residuals=[target] if P==O else [target-P,target+P]
        for R in residuals:
            queries+=1;x=None if R==O else enc(R[0])
            for tail_ids,tail in suffix.get(x,[]):
                for head_ids,head in bucket:
                    checks+=1
                    if head+tail==target:hits.add(head_ids+tail_ids)
    query=time.monotonic()-t;t=time.monotonic();direct=set()
    for ids in itertools.product(range(4),repeat=5):
        if sum((choices[j][ids[j]] for j in range(5)),O)==target:direct.add(ids)
    direct_s=time.monotonic()-t
    assert hits==direct,(index,hits,direct)
    rows.append({'box_index':index,'kind':kind,'prefix_states':64,'suffix_states':16,
                 'prefix_x_buckets':len(prefix),'suffix_x_buckets':len(suffix),
                 'residual_x_queries':queries,'candidate_group_checks':checks,
                 'verified_hits':[list(ids) for ids in sorted(hits)],
                 'precompute_seconds':prep,'query_seconds':query,'direct_seconds':direct_s})
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
        status='RSS_CAP_PARTIAL';break
result={'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],'case':case,
        'boxes_completed':len(rows),'rows':rows,'verified_hits':sum(len(x['verified_hits']) for x in rows),
        'precompute_seconds':sum(x['precompute_seconds'] for x in rows),
        'query_seconds':sum(x['query_seconds'] for x in rows),
        'direct_seconds':sum(x['direct_seconds'] for x in rows),'wall_seconds':time.monotonic()-start,
        'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(H/(case+'_protocol.json')),'script_sha256':sha(Path(__file__))}
(H/(case+'_result.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('case','status','boxes_completed','verified_hits','precompute_seconds','query_seconds','direct_seconds')},sort_keys=True),flush=True)
