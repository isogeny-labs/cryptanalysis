"""Independent Sage replay of the second x root for all 35 N41 codes."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'audit_fullroot_protocol.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
base=json.loads((HERE/'result.json').read_text())
prior=json.loads((HERE/'audit_result.json').read_text())
full=json.loads((HERE/'fullroot_result.json').read_text())
assert prior['status']=='PASS_INDEPENDENT_N41_PAIRWISE_DETERMINANT_RANK_AUDIT'
assert prior['result_sha256']==sha(HERE/'result.json')
g=json.loads((ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
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
    options=roots(g['blocks'][slot],row['masks'][0])
    fixed.append(next(root[0] for root in options if row['raw_sum'] in root))
target=hit['raw_target']
distribution=Counter()
for first,second in zip(base['charts'],full['rows']):
    assert first['mask']==second['mask']
    point=roots(g['blocks'][0],first['mask'])[1][0]
    assert point==second['root1_point']
    coords=[point]+fixed+[[target[0],target[1]^target[0]]]
    xs=[dec(p[0]) for p in coords]
    ys=[dec(p[1]) for p in coords]
    assert len(set(xs))==7 and all(E.is_on_curve(x,y) for x,y in zip(xs,ys))
    values=[]
    for sign in range(64):
        matrix=Matrix(F,7,7)
        for i,(x,y) in enumerate(zip(xs,ys)):
            if i<6 and sign>>i&1:y+=x
            matrix[i]=[F.one(),x,y,x**2,x*y,x**3,(x**2)*y]
        values.append(enc(matrix.det()))
    c=values[:]
    for bit in range(6):
        for mask in range(64):
            if mask>>bit&1:c[mask]^=c[mask^(1<<bit)]
    assert c==second['root1_coefficients']
    assert hashlib.sha256(json.dumps(c).encode()).hexdigest()==second['root1_coefficient_sha256']
    assert [s for s,value in enumerate(values) if value==0]==second['root1_zero_signs']
    non=[c[m] for m in range(1,64) if bin(m).count('1')<=3]
    total_rank=rank(first['nonconstant']+non)
    assert total_rank==second['two_root_nonconstant_rank']
    distribution[total_rank]+=1
assert dict(distribution)=={41:35}
audit={'status':'PASS_INDEPENDENT_N41_BOTH_ROOTS_DETERMINANT_RANK_AUDIT',
       'code_count':35,'rank_distribution':dict(distribution),
       'base_audit_sha256':sha(HERE/'audit_result.json'),
       'fullroot_result_sha256':sha(HERE/'fullroot_result.json'),
       'protocol_sha256':sha(HERE/'audit_fullroot_protocol.json')}
with (HERE/'audit_fullroot_result.json').open('x') as out:
    json.dump(audit,out,sort_keys=True,indent=2);out.write('\n')
print(audit['status'],flush=True)
