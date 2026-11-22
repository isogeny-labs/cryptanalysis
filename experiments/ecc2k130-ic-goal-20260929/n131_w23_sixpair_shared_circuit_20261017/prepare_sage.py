#!/usr/bin/env sage -python
"""Construct six source-correct W23 pairs and their exact group-sum control."""
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, EllipticCurve

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'n131_w23_sixpair_density_20261016/sage_audit_result.json'
poly=PolynomialRing(GF(2),'t'); t=poly.gen()
F=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
E=EllipticCurve(F,[1,0,0,0,1])
rotations=[0,18,36,54,72,90]
def dec(mask): return F(sum((t**i for i in range(mask.bit_length()) if mask>>i&1),poly.zero()))
def enc(v): return sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
def ht(v):
    out=F.zero(); q=v
    for _ in range(66): out+=q; q=q**4
    assert out**2+out==v
    return out
def point(mask):
    w=dec(mask<<1); assert w.trace()==0 and (1/w).trace()==0
    x=1+1/ht(w)
    return E.lift_x(x,all=True)[0]

edges=json.loads(SOURCE.read_text())['audited_edges']
selected=[]; used=set()
for row in edges:
    cols=set(row['columns'])
    if cols&used: continue
    selected.append(row); used|=cols
    if len(selected)==6: break
assert len(selected)==6 and len(used)==12
pairs=[]; nodes=[]
for row,rotation in zip(selected,rotations):
    a,b=row['masks']; pa,pb=point(a),point(b)
    unrot=pa+pb
    raw=E([unrot[0]**(2**rotation),unrot[1]**(2**rotation)])
    assert raw!=E(0) and raw[0]!=0
    z=1/unrot[0]
    p=dec(a<<1)*dec(b<<1); seed=dec(898618<<1); H=ht(seed)**2
    assert (1+H)*z**2+p*z+H==0
    nodes.append(raw)
    pairs.append({'masks':[a,b],'columns':row['columns'],'source_product':enc(p),
                  'output_reciprocal':enc(z),'output_inv':enc(1/z),
                  'source_inverse_product':enc(1/p)})
links=[(0,1,6),(2,3,7),(4,5,8),(6,7,9),(9,8,10)]
middle=[]
for i,j,k in links:
    q=nodes[i]+nodes[j]
    assert q!=E(0) and q[0]!=0
    nodes.append(q)
    if k!=10:middle.append(enc(1/q[0]))
Q=nodes[-1]
out={'curve_id':'EC1N131Ckb1heb5f1998f20b','seed_mask':898618,
     'rotations':rotations,'pairs':pairs,'middle_reciprocals':middle,
     'target_raw_point':[enc(Q[0]),enc(Q[1])],
     'target_reciprocal':enc(1/Q[0]),'subgroup_point':[enc((4*Q)[0]),enc((4*Q)[1])],
     'source_audit_path':str(SOURCE),'source_audit_sha256':__import__('hashlib').sha256(SOURCE.read_bytes()).hexdigest()}
(HERE/'fixture.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'PASS','pairs':len(pairs),'distinct_columns':len(used),'target_x':out['target_raw_point'][0]}))
