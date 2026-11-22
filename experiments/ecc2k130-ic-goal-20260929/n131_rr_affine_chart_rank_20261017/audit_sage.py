"""Independent Sage source, determinant, and rank replay of the affine panel."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

D=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((D/'protocol.json').read_text())
assert sha(D/'audit_sage.py')==p['source_sha256']['auditor']
panel=json.loads((D/'panel.json').read_text())
producer=json.loads((D/'result.json').read_text())
assert sha(D/'panel.json')==producer['panel_sha256']
signal.alarm(p['wall_cap_s'])
start=time.monotonic()
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(word):return F(R([(int(word)>>i)&1 for i in range(131)]))
def enc(value):return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
def xy(point):return [enc(point[0]),enc(point[1])]
def halftrace(value):
    answer=F.zero();part=value
    for _ in range(66):answer+=part;part=part**4
    assert answer**2+answer==value
    return answer
def source(mask):
    w=dec(mask<<1)
    assert w and w.trace()==0 and (1/w).trace()==0
    return E.lift_x(1+1/halftrace(w),all=True)[0]
def roots(a,b):
    outputs={}
    for P in (source(a),-source(a)):
        for Q in (source(b),-source(b)):
            S=P+Q
            assert S!=E(0)
            row=xy(S)
            outputs.setdefault(row[0],set()).add(tuple(row))
    return [[list(row) for row in sorted(outputs[x])] for x in sorted(outputs)]
def rank(words):
    return Matrix(GF(2),[[int(value>>bit&1) for bit in range(131)]
                          for value in words]).rank()
seed=p['seed_mask'];masks=panel['selection']['masks']
d1,d2=panel['selection']['directions']
assert masks==[masks[0],masks[0]^d1,masks[0]^d2,masks[0]^d1^d2]
assert len(set(masks))==4 and masks[0]^masks[1]^masks[2]^masks[3]==0
assert [roots(a,a^seed) for a in masks]==panel['selection']['roots']
target=E(*map(dec,panel['target']))
fixed=[E(*map(dec,row)) for row in panel['fixed_points']]
assert len(fixed)==5 and all(P!=E(0) for P in fixed)
all_non=[];all_values=[];all_augmented=[];rows=[]
for code,root_group in enumerate(panel['selection']['roots']):
    for root in (0,1):
        first=E(*map(dec,root_group[root][0]))
        points=[first]+fixed
        target_negative=-target
        assert len({enc(P[0]) for P in points+[target_negative]})==7
        values=[]
        for sign in range(64):
            M=Matrix(F,7,7)
            for row,P in enumerate(points+[target_negative]):
                Q=-P if row<6 and (sign>>row)&1 else P
                x,y=Q[0],Q[1]
                M[row]=[F.one(),x,y,x**2,x*y,x**3,x**2*y]
            values.append(enc(M.det()))
        coeff=values[:]
        for bit in range(6):
            for word in range(64):
                if word>>bit&1:coeff[word]^=coeff[word^(1<<bit)]
        saved=producer['rows'][2*code+root]
        assert hashlib.sha256(json.dumps(coeff).encode()).hexdigest()==saved['coefficients_sha256']
        assert [s for s,value in enumerate(values) if value==0]==saved['determinant_zero_sign_masks']
        non=[coeff[k] for k in range(1,64) if k.bit_count()<=3]
        assert all(coeff[k]==0 for k in range(64) if k.bit_count()>3)
        all_non.extend(non);all_values.extend(non+[coeff[0]])
        all_augmented.extend([(x<<1) for x in non]+[(coeff[0]<<1)|1])
        # A rank over 132 bits is the augmented rank.
        augrank=Matrix(GF(2),[[int(value>>bit&1) for bit in range(132)]
                               for value in all_augmented]).rank()
        assert rank(non)==saved['local_nonconstant_rank']
        assert rank(all_non)==saved['pooled_nonconstant_rank']
        assert rank(all_values)==saved['pooled_value_rank']
        assert augrank==saved['pooled_augmented_rank']
        rows.append({'code':code,'root':root,'pooled_nonconstant_rank':rank(all_non),
                     'common_linear_certificate':rank(all_values)==augrank,
                     'determinant_zero_sign_masks':saved['determinant_zero_sign_masks']})
assert all(row['common_linear_certificate']==producer['rows'][i]['common_linear_certificate']
           for i,row in enumerate(rows))
record={'status':'PASS_INDEPENDENT_N131_AFFINE_RR_REPLAY',
        'rows':rows,'masks':masks,'directions':[d1,d2],
        'wall_s':time.monotonic()-start,
        'self_peak_rss_bytes_darwin':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(D/'protocol.json'),
        'producer_sha256':sha(D/'result.json')}
with (D/'audit_result.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps({'status':record['status'],
                  'ranks':[row['pooled_nonconstant_rank'] for row in rows]},sort_keys=True))
