"""Eliminate two pair-output coordinates into source products at a public residual."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'
RELATION=ROOT/'n41_n131_w29_rotation_alignment_20261017/n41_audit_result.json'
PRIOR=ROOT/'n41_w9_triple_box_s3_20261017/full_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((HERE/'protocol.json').read_text())
for name,path in {'script':Path(__file__),'runtime':HERE/'sage_runtime_info.json',
                  'states':SOURCE,'relation':RELATION,'prior':PRIOR}.items():
    assert sha(path)==protocol['source_sha256'][name],name
assert not (HERE/'result.json').exists()
source=json.loads(SOURCE.read_text())
relation=json.loads(RELATION.read_text())
assert source['rotations']==[0,0,12,12,24]
assert relation['orientation']==6 and relation['state_ids']==[105,244,66,47,111]

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
seed=dec(source['seed']<<1)
h=halftrace(seed)
H1=h**2
C1=1+H1
H2=H1**(1<<12)
C2=C1**(1<<12)
assert H1 and C1 and H2 and C2

root_pairs={1:[],2:[]}
products={1:[],2:[]}
for slot in (1,2):
    for code in range(71):
        row=source['states'][slot][4*code]
        aa=dec(row['masks'][0]<<1)
        p=aa*(aa+seed)
        if slot==2:
            p=p**(1<<12)
        roots=sorted({enc(1/states[slot][sid][0])
                      for sid in range(4*code,4*code+4)})
        assert len(roots)==2
        C,H=(C1,H1) if slot==1 else (C2,H2)
        assert all(C*dec(z)**2+p*dec(z)+H==0 for z in roots)
        root_pairs[slot].append(roots)
        products[slot].append(p)
assert len({enc(v) for v in products[1]})==71
assert len({enc(v) for v in products[2]})==71

target_start=time.monotonic()
target=public-states[0][105]-states[3][47]-states[4][111]
assert target!=E(0) and target[0]
t=1/target[0]
target_setup_seconds=time.monotonic()-target_start

build_start=time.monotonic()
PQ=PolynomialRing(F,names=('p','q'))
p,q=PQ.gens()
A=PolynomialRing(PQ,'a')
a=A.gen()
f1=C1*a*a+p*a+H1
sa=1+(a*t)*(a*t)
sb=a*t
sd=a*a+t*t
M=sa*H2+C2*sd
L=sa*q+C2*sb
N=sb*H2+q*sd
G=M*M+L*N
rem=G%f1
assert rem.degree()<=1
r0=rem[0]
r1=rem[1]
eliminant=C1*r0*r0+p*r0*r1+H1*r1*r1
assert eliminant
build_seconds=time.monotonic()-build_start

scan_start=time.monotonic()
zeros=[]
eligible_zeros=[]
fixed_columns=set(source['states'][0][105]['columns']+
                  source['states'][3][47]['columns']+
                  source['states'][4][111]['columns'])
eligible_pairs=0
for i,pp in enumerate(products[1]):
    cols_i=set(source['states'][1][4*i]['columns'])
    for j,qq in enumerate(products[2]):
        cols=cols_i|set(source['states'][2][4*j]['columns'])|fixed_columns
        eligible=len(cols)==10
        eligible_pairs+=eligible
        if eliminant(pp,qq)==0:
            zeros.append([i,j])
            if eligible:
                eligible_zeros.append([i,j])
scan_seconds=time.monotonic()-scan_start

replay_start=time.monotonic()
exact=[]
for i,j in eligible_zeros:
    for ii in range(4*i,4*i+4):
        for jj in range(4*j,4*j+4):
            if states[1][ii]+states[2][jj]==target:
                exact.append([i,j,ii,jj])
assert [61,16,244,66] in exact
replay_seconds=time.monotonic()-replay_start

terms=[[list(monomial),enc(coefficient)]
       for monomial,coefficient in sorted(eliminant.dict().items())]
result={
    'status':'PASS_N41_TARGET_TWO_PRODUCT_ELIMINANT',
    'curve_id':source['curve_id'],'candidate_id':None,
    'fixed_slot_state_ids':{'0':105,'3':47,'4':111},
    'target_partial_point':[enc(target[0]),enc(target[1])],
    'target_reciprocal':enc(t),
    'pair_equation_constants':{'C1':enc(C1),'H1':enc(H1),
                               'C2':enc(C2),'H2':enc(H2)},
    'eliminant_terms':terms,
    'term_count':len(terms),
    'degree_p':max(m[0][0] for m in terms),
    'degree_q':max(m[0][1] for m in terms),
    'source_code_count_per_slot':71,
    'product_pairs_tested':71*71,
    'column_eligible_product_pairs':eligible_pairs,
    'algebraic_zero_code_pairs':zeros,
    'column_eligible_algebraic_zero_pairs':eligible_zeros,
    'exact_state_witnesses':exact,
    'target_setup_seconds':target_setup_seconds,
    'target_eliminant_build_seconds':build_seconds,
    'target_pair_scan_seconds':scan_seconds,
    'target_exact_replay_seconds':replay_seconds,
    'target_total_seconds':target_setup_seconds+build_seconds+scan_seconds+replay_seconds,
    'self_maxrss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256':sha(HERE/'protocol.json'),
    'source_sha256':{'script':sha(Path(__file__)),
                     'runtime':sha(HERE/'sage_runtime_info.json'),
                     'states':sha(SOURCE),'prior':sha(PRIOR)},
}
(HERE/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in
                  ('status','term_count','degree_p','degree_q',
                   'column_eligible_product_pairs',
                   'algebraic_zero_code_pairs','exact_state_witnesses',
                   'target_total_seconds')}))
