"""Independent Sage determinant and GF(2)-rank replay for four W23 charts."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'audit_protocol_n131.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
panel=json.loads((HERE/'panel_n131_v2.json').read_text())
producer=json.loads((HERE/'result_n131_v2.json').read_text())
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(word):return F(R([(int(word)>>i)&1 for i in range(131)]))
def enc(value):return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
def valid(point):
    x,y=map(dec,point)
    return E.is_on_curve(x,y)
target=panel['target']
assert valid(target)
rows=[]
pooled=[]
for variant,saved in zip(panel['variants'],producer['rows']):
    points=[variant['roots'][0][0]]+panel['fixed_points']
    assert all(valid(point) for point in points)
    coords=points+[[target[0],target[1]^target[0]]]
    xs=[dec(point[0]) for point in coords]
    ys=[dec(point[1]) for point in coords]
    assert len(set(xs))==7
    values=[]
    for sign in range(64):
        matrix=Matrix(F,7,7)
        for i,(x,y) in enumerate(zip(xs,ys)):
            y=y+((sign>>i)&1)*x if i<6 else y
            matrix[i]=[F.one(),x,y,x**2,x*y,x**3,(x**2)*y]
        values.append(enc(matrix.det()))
    coefficients=values[:]
    for bit in range(6):
        for mask in range(64):
            if mask>>bit&1:coefficients[mask]^=coefficients[mask^(1<<bit)]
    assert all(coefficients[mask]==0 for mask in range(64) if bin(mask).count('1')>3)
    assert hashlib.sha256(json.dumps(coefficients).encode()).hexdigest()==saved['coefficient_sha256']
    non=[coefficients[mask] for mask in range(1,64) if bin(mask).count('1')<=3]
    pooled.extend(non)
    def rank(words,width):
        return Matrix(GF(2),[[int(word>>j&1) for j in range(width)] for word in words]).rank()
    local_rank=rank(non,131)
    pooled_rank=rank(pooled,131)
    assert local_rank==saved['local_nonconstant_rank']==34
    assert pooled_rank==saved['pooled_nonconstant_rank']
    assert [i for i,value in enumerate(values) if value==0]==saved['determinant_zero_sign_masks']
    rows.append({'sample_index':variant['sample_index'],'masks':variant['masks'],
                 'local_rank':local_rank,'pooled_rank':pooled_rank,
                 'coefficient_sha256':saved['coefficient_sha256']})
assert [row['pooled_rank'] for row in rows]==[34,68,102,131]
result={'status':'PASS_INDEPENDENT_N131_DETERMINANT_RANK_REPLAY',
        'rows':rows,'protocol_sha256':sha(HERE/'audit_protocol_n131.json'),
        'producer_sha256':sha(HERE/'result_n131_v2.json')}
with (HERE/'audit_result_n131.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'],flush=True)
