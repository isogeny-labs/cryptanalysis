"""Build target-conditioned quartic norms over affine left-code blocks."""
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


protocol=json.loads((HERE/'protocol.json').read_text())
for path,digest in protocol['sources'].items():
    assert sha(path)==digest,path
assert not (HERE/'result.json').exists()
signal.signal(signal.SIGALRM,lambda _s,_f:(_ for _ in ()).throw(TimeoutError('symbolic norm wall cap')))
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
assert len(H.monomials())==13
seed=dec(source['seed']<<1)
free_bits=[0,1,2,3,4,6,7,8]
basis=[]
for bit in free_bits:
    a=dec(1<<(bit+1))
    basis.append(a*a+seed*a)


def product(code,rotation=0):
    value=sum((basis[i] for i in range(8) if code>>i&1),F.zero())
    return value**(1<<rotation)


reference_code=protocol['reference_left_raw_code']
ref_state=source['states'][1][244]
assert sum(((ref_state['masks'][0]>>bit)&1)<<i
           for i,bit in enumerate(free_bits))==reference_code
q_state=source['states'][2][66]
right_code=sum(((q_state['masks'][0]>>bit)&1)<<i
               for i,bit in enumerate(free_bits))
q_root=product(right_code,12)
assert H(product(reference_code),q_root)==0
variable_indices=protocol['variable_code_bit_indices']
variable_mask=sum(1<<i for i in variable_indices)
base_code=reference_code&~variable_mask
base_p=product(base_code)
assert base_code==protocol['positive_block_base_code']
assert reference_code==base_code|(reference_code&variable_mask)
right_basis=[value**(1<<12) for value in basis]
Q=PolynomialRing(F,'x')
x=Q.gen()
L=x
for b in right_basis:
    L=L**2+L(b)*L
assert L.degree()==256
Lcoeff=[L[1<<i] for i in range(9)]


def subspace_gcd_degree(f):
    power=x%f
    remainder=Q.zero()
    for i,c in enumerate(Lcoeff):
        remainder+=c*power
        if i<8:
            power=power**2%f
    return int(f.gcd(remainder).degree())


rows=[]
current=H
for k in range(0,protocol['max_width']+1):
    row_start=time.monotonic()
    # Specialize p first; the resulting q polynomial is compared with a
    # separately enumerated product over the same affine code block.
    f=Q.zero()
    for (i,j),coefficient in current.dict().items():
        f+=coefficient*base_p**i*x**j
    explicit=Q.one()
    for mask in range(1<<k):
        code=base_code
        for bit_index in range(k):
            if mask>>bit_index&1:
                code^=1<<variable_indices[bit_index]
        value=product(code)
        hq=Q.zero()
        for (i,j),coefficient in H.dict().items():
            hq+=coefficient*value**i*x**j
        explicit*=hq
    assert f==explicit
    assert f(q_root)==0
    gcd_degree=subspace_gcd_degree(f)
    assert gcd_degree>=1
    rows.append({'width':k,'block_code_count':1<<k,
                 'norm_monomials':len(current.dict()),
                 'degree_p':int(current.degree(p)),
                 'degree_q':int(current.degree(q)),
                 'specialized_degree_q':int(f.degree()),
                 'gcd_degree':gcd_degree,
                 'specialize_explicit_and_gcd_seconds':time.monotonic()-row_start,
                 'cumulative_wall_seconds':time.monotonic()-started})
    print(json.dumps({'phase':'width','row':rows[-1]}),flush=True)
    if k<protocol['max_width']:
        shift=basis[variable_indices[k]]
        next_start=time.monotonic()
        current=current*current(p+shift,q)
        rows[-1]['next_norm_build_seconds']=time.monotonic()-next_start
signal.alarm(0)
result={'status':'PASS_N41_SYMBOLIC_LEFT_BLOCK_NORM','candidate_id':None,
        'curve_id':protocol['curve_id'],'reference_codes':[reference_code,right_code],
        'positive_block_base_code':base_code,'rows':rows,
        'total_wall_seconds':time.monotonic()-started,
        'self_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'protocol.json')}
(HERE/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'total_wall_seconds':result['total_wall_seconds']}))
