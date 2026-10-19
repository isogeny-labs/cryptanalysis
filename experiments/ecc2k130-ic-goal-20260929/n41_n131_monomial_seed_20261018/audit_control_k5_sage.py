"""Independent Sage group replay of the k5 five-pair control."""
import hashlib,json
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'audit_control_k5_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_INDEPENDENT_REPLAY'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
control=json.loads((HERE/'control_k5.json').read_text())
R=PolynomialRing(GF(2),'v');v=R.gen()
F=GF(2**131,name='v',modulus=v**131+v**13+v**2+v+1)
E=EllipticCurve(F,[1,0,0,0,1])
enc=lambda a:sum(int(bit)<<i for i,bit in enumerate(a.polynomial().list()))
ht=lambda a:sum((a**(1<<(2*i)) for i in range(66)),F.zero())
def col(point):
    x=point[0];values=[]
    for _ in range(131):values.append(enc(x));x=x*x
    return min(values)
nodes=[];cols=[];middle=[]
seed=528;h=ht(F.from_integer(seed<<1))
assert h==F(v**5) and h.trace()==0
for row,rot in zip(control['pairs'],[0,18,36,54,72]):
    a,b=row['masks'];assert a<b and a^b==seed
    w1,w2=F.from_integer(a<<1),F.from_integer(b<<1)
    assert not w1.trace() and not w2.trace()
    assert not (1/w1).trace() and not (1/w2).trace()
    p1=E.lift_x(1+1/ht(w1),all=True)[0]
    p2=E.lift_x(1+1/ht(w2),all=True)[0]
    these=[col(p1),col(p2)]
    assert these==row['folded_column_representatives']
    cols.extend(these)
    q=p1+p2;assert q!=E(0) and q[0]
    product=w1*w2;z=1/q[0]
    assert enc(product)==row['source_product']
    assert enc(1/product)==row['source_inverse_product']
    assert enc(z)==row['output_reciprocal']
    assert (1+h*h)*z*z+product*z+h*h==0
    nodes.append(E(q[0]**(1<<rot),q[1]**(1<<rot)))
assert len(set(cols))==10 and control['pairs'][0]['masks'][0]&255==3
for i,j,k in ((0,1,5),(5,2,6),(3,4,7),(6,7,8)):
    q=nodes[i]+nodes[j];assert q!=E(0) and q[0]
    nodes.append(q)
    if k!=8:middle.append(enc(1/q[0]))
assert middle==control['middle_reciprocals']
target=nodes[-1]
assert [enc(target[0]),enc(target[1])]==control['target_raw_point']
assert enc(1/target[0])==control['target_reciprocal']
assert [enc((4*target)[0]),enc((4*target)[1])]==control['subgroup_point']
result={'status':'PASS_INDEPENDENT_K5_CONTROL_GROUP_REPLAY','curve_id':control['curve_id'],
        'seed_mask':seed,'distinct_folded_columns':len(set(cols)),
        'raw_target':control['target_raw_point'],'subgroup_target':control['subgroup_point'],
        'protocol_sha256':sha(HERE/'audit_control_k5_protocol.json'),'auditor_sha256':sha(Path(__file__))}
(HERE/'audit_control_k5_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
