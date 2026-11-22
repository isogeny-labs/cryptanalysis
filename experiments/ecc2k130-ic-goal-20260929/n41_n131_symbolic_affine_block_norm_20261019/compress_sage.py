"""Compress an affine-code quartic norm through its linearized invariant."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol=json.loads((HERE/'compress_protocol.json').read_text())
for path,digest in protocol['sources'].items():
    assert sha(path)==digest,path
assert not (HERE/'compress_result.json').exists()
signal.signal(signal.SIGALRM,lambda _s,_f:(_ for _ in ()).throw(TimeoutError('compressed norm wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started=time.monotonic()
source=json.loads(Path(protocol['source_states']).read_text())
prior=json.loads(Path(protocol['eliminant']).read_text())
S=PolynomialRing(GF(2),'u')
u=S.gen()
F=GF(2**41,name='u',modulus=u**41+u**3+1)


def dec(word):
    return F(S([(int(word)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(c)<<i for i,c in enumerate(value.polynomial().list()))


R=PolynomialRing(F,names=('p','q'))
p,q=R.gens()
H=sum((dec(coef)*p**exps[0]*q**exps[1]
       for exps,coef in prior['eliminant_terms']),R.zero())
seed=dec(source['seed']<<1)
free_bits=[0,1,2,3,4,6,7,8]
basis=[]
for bit in free_bits:
    a=dec(1<<(bit+1))
    basis.append(a*a+seed*a)


def product(code,rotation=0):
    value=sum((basis[i] for i in range(8) if code>>i&1),F.zero())
    return value**(1<<rotation)


variable_indices=protocol['variable_code_bit_indices']
assert variable_indices==[2,0,1,3]
norm_start=time.monotonic()
N=H
for index in variable_indices:
    N=N*N(p+basis[index],q)
norm_seconds=time.monotonic()-norm_start
assert N.degree(p)==64 and N.degree(q)==64

# L_B has the affine block's translation space as its exact roots.
U=PolynomialRing(F,'X')
X=U.gen()
LB=X
for index in variable_indices:
    LB=LB**2+LB(basis[index])*LB
assert LB.degree()==16
LB_R=sum((coefficient*p**i for i,coefficient in LB.dict().items()),R.zero())
assert all(LB(value)==0 for value in
           (product(code) for code in range(16)))

# Since N is translation-invariant, polynomial division by the monic L_B
# must leave only powers of L_B and no residual p-coordinate terms.
compress_start=time.monotonic()
residual=N
coefficients={}
for power in range(4,-1,-1):
    exponent=16*power
    assert not residual or residual.degree(p)<=exponent
    coefficient=sum((value*q**j for (i,j),value in residual.dict().items()
                     if i==exponent),R.zero())
    coefficients[power]=coefficient
    residual-=coefficient*LB_R**power
assert residual==0
compact_terms=sum(len(coefficient.dict()) for coefficient in coefficients.values())
compress_seconds=time.monotonic()-compress_start

Q=PolynomialRing(F,'x')
x=Q.gen()
right_basis=[value**(1<<12) for value in basis]
Lq=x
for b in right_basis:
    Lq=Lq**2+Lq(b)*Lq
assert Lq.degree()==256
Lq_coeff=[Lq[1<<i] for i in range(9)]


def qpoly(expr,pvalue):
    out=Q.zero()
    for (i,j),value in expr.dict().items():
        out+=value*pvalue**i*x**j
    return out


def fast_gcd_degree(f):
    power=x%f
    remainder=Q.zero()
    for i,coefficient in enumerate(Lq_coeff):
        remainder+=coefficient*power
        if i<8:
            power=power**2%f
    return int(f.gcd(remainder).degree())


q_state=source['states'][2][66]
q_code=sum(((q_state['masks'][0]>>bit)&1)<<i
           for i,bit in enumerate(free_bits))
q_root=product(q_code,12)
rows=[]
for prefix in range(16):
    base_code=prefix<<4
    base_p=product(base_code)
    invariant=LB(base_p)
    start_comp=time.monotonic()
    compact=Q.zero()
    for power,expr in coefficients.items():
        compact+=invariant**power*qpoly(expr,F.one())
    compact_seconds=time.monotonic()-start_comp
    start_full=time.monotonic()
    full=qpoly(N,base_p)
    full_seconds=time.monotonic()-start_full
    start_explicit=time.monotonic()
    explicit=Q.one()
    for offset in range(16):
        explicit*=qpoly(H,product(base_code|offset))
    explicit_seconds=time.monotonic()-start_explicit
    assert compact==full==explicit
    gcd_start=time.monotonic()
    gcd_degree=fast_gcd_degree(compact)
    gcd_seconds=time.monotonic()-gcd_start
    if prefix==protocol['positive_prefix']:
        assert compact(q_root)==0 and gcd_degree>=1
    rows.append({'prefix':prefix,'base_code':base_code,
                 'gcd_degree':gcd_degree,
                 'compact_specialization_seconds':compact_seconds,
                 'full_specialization_seconds':full_seconds,
                 'explicit_product_seconds':explicit_seconds,
                 'gcd_seconds':gcd_seconds})
    print(json.dumps({'prefix':prefix,'gcd_degree':gcd_degree,
                      'elapsed_seconds':time.monotonic()-started}),flush=True)
signal.alarm(0)
result={'status':'PASS_N41_COMPRESSED_AFFINE_BLOCK_NORM','candidate_id':None,
        'curve_id':protocol['curve_id'],'norm_monomials':len(N.dict()),
        'invariant_degree':int(LB.degree()),'compact_monomials':compact_terms,
        'compact_coefficient_supports':{str(k):len(v.dict()) for k,v in coefficients.items()},
        'norm_build_seconds':norm_seconds,'compress_seconds':compress_seconds,
        'rows':rows,'positive_prefix':protocol['positive_prefix'],
        'retained_prefixes':[row['prefix'] for row in rows if row['gcd_degree']>0],
        'total_wall_seconds':time.monotonic()-started,
        'self_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'compress_protocol.json')}
(HERE/'compress_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'norm_monomials':result['norm_monomials'],
                  'compact_monomials':compact_terms,
                  'retained_prefixes':result['retained_prefixes'],
                  'total_wall_seconds':result['total_wall_seconds']}))
