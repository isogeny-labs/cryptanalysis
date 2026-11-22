"""Independent Sage determinants and GF(2) ranks for all 35 N41 charts."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'audit_protocol.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
result=json.loads((HERE/'result.json').read_text())
geometry=json.loads((ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
hit=json.loads((ROOT/'n41_sixpair_shared_target_20261017/join_audit_result.json').read_text())
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**41,name='t',modulus=t**41+t**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(word):return F(R([(int(word)>>i)&1 for i in range(41)]))
def enc(value):return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
def rank(words):
    return Matrix(GF(2),[[int(word>>j&1) for j in range(41)] for word in words]).rank()
def roots(block,mask):
    by_x={}
    for row in block['states']:
        if row['a']==mask:
            x,y=row['raw_sum'];by_x.setdefault(x,set()).add(y)
    assert len(by_x)==2 and all(len(ys)==2 for ys in by_x.values())
    return [[[x,y] for y in sorted(by_x[x])] for x in sorted(by_x)]
fixed=[]
for slot in range(1,6):
    row=hit['pair_rows'][slot]
    matching=[root for root in roots(geometry['blocks'][slot],row['masks'][0])
              if row['raw_sum'] in root]
    assert len(matching)==1
    fixed.append(matching[0][0])
target=hit['raw_target']
assert target==protocol['raw_target']==result['raw_target']
coefficients=[];nonconstant=[]
for chart in result['charts']:
    assert chart['point']==roots(geometry['blocks'][0],chart['mask'])[0][0]
    points=[chart['point']]+fixed
    coords=points+[[target[0],target[1]^target[0]]]
    xs=[dec(row[0]) for row in coords]
    ys=[dec(row[1]) for row in coords]
    assert len(set(xs))==7
    assert all(E.is_on_curve(x,y) for x,y in zip(xs,ys))
    values=[]
    for sign in range(64):
        m=Matrix(F,7,7)
        for i,(x,y) in enumerate(zip(xs,ys)):
            if i<6 and sign>>i&1:y+=x
            m[i]=[F.one(),x,y,x**2,x*y,x**3,(x**2)*y]
        values.append(enc(m.det()))
    c=values[:]
    for bit in range(6):
        for mask in range(64):
            if mask>>bit&1:c[mask]^=c[mask^(1<<bit)]
    assert all(c[mask]==0 for mask in range(64) if bin(mask).count('1')>3)
    assert hashlib.sha256(json.dumps(c).encode()).hexdigest()==chart['coefficient_sha256']
    assert c==chart['coefficients']
    assert [s for s,value in enumerate(values) if value==0]==chart['zero_signs']
    row=[c[mask] for mask in range(1,64) if bin(mask).count('1')<=3]
    assert rank(row)==34
    coefficients.append(c);nonconstant.append(row)
assert len(coefficients)==35
distribution=Counter()
for i in range(35):
    for j in range(i+1,35):
        distribution[rank(nonconstant[i]+nonconstant[j])]+=1
assert dict(distribution)=={41:595}
assert {int(k):v for k,v in result['pair_nonconstant_rank_distribution'].items()}==dict(distribution)
audit={'status':'PASS_INDEPENDENT_N41_PAIRWISE_DETERMINANT_RANK_AUDIT',
       'chart_count':35,'pair_count':595,'pair_rank_distribution':dict(distribution),
       'result_sha256':sha(HERE/'result.json'),'protocol_sha256':sha(HERE/'audit_protocol.json')}
with (HERE/'audit_result.json').open('x') as out:
    json.dump(audit,out,sort_keys=True,indent=2);out.write('\n')
print(audit['status'],flush=True)
