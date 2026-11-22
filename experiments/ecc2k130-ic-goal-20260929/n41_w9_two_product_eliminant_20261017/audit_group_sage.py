"""Independent all-pair curve-law check of the saved eliminant."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((HERE/'group_audit_protocol.json').read_text())
for key,path in {'script':Path(__file__),'runtime':HERE/'group_audit_runtime_info.json',
                 'states':SOURCE,'producer':HERE/'result.json'}.items():
    assert sha(path)==protocol['source_sha256'][key],key
assert not (HERE/'group_audit_result.json').exists()
source=json.loads(SOURCE.read_text())
producer=json.loads((HERE/'result.json').read_text())

K=PolynomialRing(GF(2),'u')
u=K.gen()
F=GF(2**41,name='u',modulus=u**41+u**3+1)
E=EllipticCurve(F,[1,0,0,0,1])


def dec(word):
    return F(K([(int(word)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(c)<<i for i,c in enumerate(value.polynomial().list()))


def halftrace(value):
    original=value
    out=F.zero()
    for _ in range(21):
        out+=value
        value=value**4
    assert out**2+out==original
    return out


states=[[E(dec(row['point'][0]),dec(row['point'][1])) for row in slot]
        for slot in source['states']]
raw=E(dec(source['target_raw_point'][0]),dec(source['target_raw_point'][1]))
public=E(raw[0]**(1<<6),raw[1]**(1<<6))
target=public-states[0][105]-states[3][47]-states[4][111]
assert target!=E(0) and target[0]
assert producer['target_partial_point']==[enc(target[0]),enc(target[1])]

seed=dec(source['seed']<<1)
h=halftrace(seed)
H1=h*h
C1=1+H1
H2=H1**(1<<12)
C2=C1**(1<<12)
assert producer['pair_equation_constants']=={
    'C1':enc(C1),'H1':enc(H1),'C2':enc(C2),'H2':enc(H2)}

products={1:[],2:[]}
for slot in (1,2):
    C,H=(C1,H1) if slot==1 else (C2,H2)
    for code in range(71):
        mask=dec(source['states'][slot][4*code]['masks'][0]<<1)
        p=mask*(mask+seed)
        if slot==2:
            p=p**(1<<12)
        roots={1/states[slot][sid][0] for sid in range(4*code,4*code+4)}
        assert len(roots)==2
        assert all(C*z*z+p*z+H==0 for z in roots)
        products[slot].append(p)

coefficients=[(degree[0],degree[1],dec(word))
              for degree,word in producer['eliminant_terms']]


def evaluate(p,q):
    return sum((coefficient*(p**i)*(q**j) for i,j,coefficient in coefficients),F.zero())


start=time.monotonic()
zeros=[]
eligible_zeros=[]
exact=[]
eligible_count=0
fixed=set(source['states'][0][105]['columns']+
          source['states'][3][47]['columns']+
          source['states'][4][111]['columns'])
for i,p in enumerate(products[1]):
    for j,q in enumerate(products[2]):
        columns=fixed|set(source['states'][1][4*i]['columns'])|set(source['states'][2][4*j]['columns'])
        eligible=len(columns)==10
        eligible_count+=eligible
        algebraic=evaluate(p,q)==0
        if algebraic:
            zeros.append([i,j])
            if eligible:
                eligible_zeros.append([i,j])
        group_hit=[]
        for ii in range(4*i,4*i+4):
            for jj in range(4*j,4*j+4):
                if states[1][ii]+states[2][jj]==target:
                    group_hit.append([i,j,ii,jj])
        if group_hit:
            assert algebraic and eligible
            exact+=group_hit

assert eligible_count==producer['column_eligible_product_pairs']==4550
assert zeros==producer['algebraic_zero_code_pairs']==[[61,16]]
assert eligible_zeros==producer['column_eligible_algebraic_zero_pairs']==[[61,16]]
assert exact==producer['exact_state_witnesses']==[[61,16,244,66]]
result={
    'status':'PASS_INDEPENDENT_N41_ELIMINANT_ALL_PAIR_GROUP_REPLAY',
    'product_pairs_checked':71*71,
    'signed_pair_assignments_checked':71*71*16,
    'column_eligible_product_pairs':eligible_count,
    'algebraic_zero_pairs':zeros,
    'exact_state_witnesses':exact,
    'elapsed_seconds':time.monotonic()-start,
    'self_maxrss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256':sha(HERE/'group_audit_protocol.json'),
    'source_sha256':{'producer':sha(HERE/'result.json'),
                     'states':sha(SOURCE)},
}
(HERE/'group_audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({key:result[key] for key in
                  ('status','product_pairs_checked','signed_pair_assignments_checked',
                   'algebraic_zero_pairs','exact_state_witnesses')}))
