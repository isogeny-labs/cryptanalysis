"""Construct independent source-valid N131 k5 five-pair assignment."""
import hashlib,json,random
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'control_k5_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_CONTROL'
for name,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],name
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
E=EllipticCurve(F,[1,0,0,0,1])
seed=528;wseed=F.from_integer(seed<<1)
ht=lambda v:sum((v**(1<<(2*i)) for i in range(66)),F.zero())
enc=lambda v:sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
def col(point):
    x=point[0]; values=[]
    for _ in range(131):values.append(enc(x));x=x*x
    return min(values)
def source(mask):
    w=F.from_integer(mask<<1)
    if not w or w.trace() or (1/w).trace():return None
    h=ht(w)
    assert h*h+h==w and h
    return E.lift_x(1+1/h,all=True)[0]
rng=random.Random(cfg['rng_seed'])
selected=[];used=set();attempts=0
free=[i for i in range(29) if i!=9]
while len(selected)<5 and attempts<cfg['attempt_cap']:
    attempts+=1
    if not selected:
        a=3+sum(rng.getrandbits(1)<<bit for bit in free if bit>=8)
    else:
        a=sum(rng.getrandbits(1)<<bit for bit in free)
    b=a^seed
    if not (0<a<b<(1<<29)):continue
    pa,pb=source(a),source(b)
    if pa is None or pb is None:continue
    ca,cb=col(pa),col(pb)
    if ca==cb or ca in used or cb in used:continue
    pair=pa+pb
    if pair==E(0) or not pair[0]:continue
    selected.append((a,b,pa,pb,ca,cb,pair))
    used.update((ca,cb))
assert len(selected)==5 and len(used)==10
assert selected[0][0]&255==3
h=ht(wseed)
assert h==F(t**5) and h.trace()==0 and h*h+h==wseed
rows=[];nodes=[]
for rotation,(a,b,pa,pb,ca,cb,pair) in zip([0,18,36,54,72],selected):
    z=1/pair[0];product=F.from_integer(a<<1)*F.from_integer(b<<1)
    assert (1+h*h)*z*z+product*z+h*h==0
    rows.append({'masks':[a,b],'folded_column_representatives':[ca,cb],
                 'source_product':enc(product),'source_inverse_product':enc(1/product),
                 'output_reciprocal':enc(z)})
    nodes.append(E(pair[0]**(1<<rotation),pair[1]**(1<<rotation)))
middle=[]
for i,j,k in ((0,1,5),(5,2,6),(3,4,7),(6,7,8)):
    q=nodes[i]+nodes[j]
    assert q!=E(0) and q[0]
    nodes.append(q)
    if k!=8:middle.append(enc(1/q[0]))
target=nodes[-1]
result={'status':'COMPLETE_CONSTRUCTED_K5_CONTROL','candidate_id':None,
        'curve_id':'EC1N131Ckb1heb5f1998f20b','seed_mask':seed,'attempts':attempts,
        'pairs':rows,'middle_reciprocals':middle,'target_raw_point':[enc(target[0]),enc(target[1])],
        'target_reciprocal':enc(1/target[0]),'subgroup_point':[enc((4*target)[0]),enc((4*target)[1])],
        'distinct_folded_columns':len(used),'protocol_sha256':sha(HERE/'control_k5_protocol.json'),
        'script_sha256':sha(Path(__file__))}
(HERE/'control_k5.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','attempts','target_raw_point','distinct_folded_columns')},sort_keys=True))
