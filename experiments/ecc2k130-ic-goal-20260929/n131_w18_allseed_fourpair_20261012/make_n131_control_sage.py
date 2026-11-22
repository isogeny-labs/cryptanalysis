"""Independent checked-Sage constructed diagonal four-pair chart at N131."""
import hashlib,json
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing
h=Path(__file__).resolve().parent;root=h.parent
p=json.loads((h/'n131_control_protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
support=root/'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv'
paths={'source':Path(__file__),'support':support,'runtime':h/'n131_control_sage_runtime_info.json'}
assert {k:sha(v) for k,v in paths.items()}==p['sha256']
columns={int(m):int(c) for m,c in (line.split() for line in support.read_text().splitlines())}
assert len(columns)==131307
ring=PolynomialRing(GF(2),'t');t=ring.gen();F=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
E=EllipticCurve(F,[1,0,0,0,1]);O=E(0)
def dec(n):return F(ring([(int(n)>>i)&1 for i in range(131)]))
def enc(v):return sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
def halftrace(w):
    v=F.zero();z=w
    for _ in range(66):v+=z;z=z**4
    assert v**2+v==w
    return v
def diagonal(mask):
    w=dec(mask<<1);assert w.trace()==0
    u=halftrace(w);assert u!=0
    x=1+1/u
    raw=E.lift_x(x,all=True)[0]
    P=raw+E(raw[0]**2,raw[1]**2)
    assert P!=O and P[0]==1/w
    return P
rotations=(0,32,64,96)
ordered=sorted(columns)
chosen=[];occupied=set()
for m in ordered:
    c=columns[m]
    if c not in occupied:
        chosen.append(m);occupied.add(c)
    if len(chosen)==64:break
assert len(chosen)==64
for start in range(57):
    masks=chosen[start:start+8]
    pairs=[]
    for i in range(4):
        P=diagonal(masks[2*i])+diagonal(masks[2*i+1])
        if P==O or P[0]==0:break
        pairs.append(E(P[0]**(1<<rotations[i]),P[1]**(1<<rotations[i])))
    if len(pairs)!=4:continue
    middle=[pairs[0]+pairs[1],pairs[2]+pairs[3]]
    target=middle[0]+middle[1]
    if any(P==O or P[0]==0 for P in middle+[target]):continue
    break
else:raise RuntimeError('no nonexceptional constructed chart in frozen prefix')
r=680564733841876926932320129493409985129
assert r*(4*target)==O
result={'status':'PASS_N131_DIAGONAL_ALLSEED_FOURPAIR_CONSTRUCTED_CHART',
        'curve_id':'EC1N131Ckb1heb5f1998f20b','selected_window_start':start,
        'masks':[masks[2*i:2*i+2] for i in range(4)],
        'columns':[columns[m] for m in masks],
        'sign_bits':[[0,0] for _ in range(4)],'rotations':list(rotations),
        'pair_points':[[enc(P[0]),enc(P[1])] for P in pairs],
        'pair_reciprocals':[enc(1/P[0]) for P in pairs],
        'intermediate_reciprocals':[enc(1/P[0]) for P in middle],
        'raw_target':[enc(target[0]),enc(target[1])],
        'public_target':[enc((4*target)[0]),enc((4*target)[1])],
        'target_reciprocal':enc(1/target[0]),
        'source_hashes':{k:sha(v) for k,v in paths.items()}}
(h/'n131_control_fixture.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(result['status'],start,flush=True)
