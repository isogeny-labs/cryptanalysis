"""Independent N131 Sage replay of degree-three family certificates."""
import hashlib,json,time
from itertools import combinations,product
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'n131_audit_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_INDEPENDENT_N131_AUDIT'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
run=json.loads((HERE/'n131_result.json').read_text())
assert run['status']=='COMPLETE_N131_W29_FAMILY_PANEL' and len(run['rows'])==12
source=json.loads(Path(cfg['sources']['coefficients']['path']).read_text())
assert source['rows'][0]['point']==cfg['constructed_target']
assert source['rows'][1]['point']==cfg['frozen_public_raw_point']
R=PolynomialRing(GF(2),'v');v=R.gen()
F=GF(2**131,name='v',modulus=v**131+v**13+v**2+v+1)
E=EllipticCurve(F,[1,0,0,0,1])
enc=lambda x:sum(int(c)<<i for i,c in enumerate(x.polynomial().list()))
dec=lambda x:F.from_integer(x)
seedmask=898618;seed=dec(seedmask<<1)
bits=[i for i in range(29) if i!=seedmask.bit_length()-1]
assert len(bits)==28
def code_mask(code):return sum(((code>>j)&1)<<bit for j,bit in enumerate(bits))
def src_product(code,rotation):
    a=dec(code_mask(code)<<1)
    return (a*a+seed*a)**(1<<rotation)
def valid_point(mask):
    w=dec(mask<<1)
    assert w and w.trace()==0 and (1/w).trace()==0
    h=sum((w**(1<<(2*i)) for i in range(66)),F.zero())
    assert h*h+h==w and h
    return E.lift_x(1+1/h,all=True)[0]
for code in cfg['p_codes']:
    mask=code_mask(code);assert 0<mask<mask^seedmask<(1<<29)
    valid_point(mask);valid_point(mask^seedmask)
qbasis=[]
for bit in bits:
    a=dec(1<<(bit+1));qbasis.append((a*a+seed*a)**(1<<18))
assert src_product(16722,18)==source['rows'][0]['positive_pair_products'][1]
mons=[0]+[1<<i for i in range(28)]+[(1<<i)|(1<<j) for i,j in combinations(range(28),2)]
assert len(mons)==407
terms=[{(i,j):dec(c) for i,j,c in row['terms']} for row in source['rows'][:2]]
start=time.monotonic();checked=0;rejected=0;positive=0
for row in run['rows']:
    if time.monotonic()-start>cfg['wall_cap_seconds']:
        raise TimeoutError('N131 independent audit wall cap')
    ti=row['target_index'];p=src_product(row['p_code'],0)
    assert enc(p)==row['p_product']
    pp=[F.one(),p]
    for _ in range(3):pp.append(pp[-1]*p)
    byj=[F.zero() for _ in range(5)]
    for (i,j),c in terms[ti].items():byj[j]+=c*pp[i]
    def evaluate(q):
        qq=[F.one(),q]
        for _ in range(3):qq.append(qq[-1]*q)
        return sum((byj[j]*qq[j] for j in range(5)),F.zero())
    constant=evaluate(F.zero())
    single=[evaluate(q)+constant for q in qbasis]
    doubles=[evaluate(qbasis[i]+qbasis[j])+single[i]+single[j]+constant
             for i,j in combinations(range(28),2)]
    coeffs=[enc(x) for x in [constant,*single,*doubles]]
    for qcode in cfg['expansion_check_qcodes']:
        q=sum((qbasis[j] for j in range(28) if qcode>>j&1),F.zero())
        expanded=0
        for mask,c in zip(mons,coeffs):
            if qcode&mask==mask:expanded^=c
        assert expanded==enc(evaluate(q))
    if row['reject']:
        poly={}
        for bit,j in row['certificate_rows']:
            assert 0<=bit<131 and -1<=j<28
            multiplier=0 if j<0 else 1<<j
            for mask,c in zip(mons,coeffs):
                if c>>bit&1:
                    mm=mask|multiplier
                    poly[mm]=poly.get(mm,0)^1
        assert {m:b for m,b in poly.items() if b}=={0:1}
        assert row['sample_zero_q_codes']==[]
        rejected+=1
    else:
        assert ti==0 and row['p_code']==3 and row['certificate_rows'] is None
        assert 16722 in row['sample_zero_q_codes']
        assert evaluate(src_product(16722,18))==0
        positive+=1
    checked+=1
assert checked==12 and rejected==11 and positive==1
# Replay the constructed positive as two signed pair sums with ten code bits free in the algebraic gate.
def signed_pair(code,rotation):
    mask=code_mask(code);a=valid_point(mask);b=valid_point(mask^seedmask)
    out=[]
    for sa,sb in product((0,1),repeat=2):
        q=(-a if sa else a)+(-b if sb else b)
        assert q!=E(0)
        out.append(E(q[0]**(1<<rotation),q[1]**(1<<rotation)))
    return out
left=signed_pair(3,0);right=signed_pair(16722,18)
target=E(*map(dec,cfg['constructed_target']))
group_hits=sum(a+b==target for a in left for b in right)
assert group_hits>=1
result={'status':'PASS_INDEPENDENT_N131_MACAULAY_PANEL','rows_checked':checked,
        'rejected_certificates_checked':rejected,'positive_families_preserved':positive,
        'constructed_group_sign_hits':group_hits,'wall_seconds':time.monotonic()-start,
        'audit_protocol_sha256':sha(HERE/'n131_audit_protocol.json'),
        'auditor_sha256':sha(Path(__file__))}
(HERE/'n131_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True),flush=True)
