"""Compare quartic roots with compact linearized-subspace GCD per first code."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((HERE/'root_probe_protocol_v2.json').read_text())
for key,path in {'script':Path(__file__),'runtime':HERE/'root_probe_runtime_info_v2.json',
                 'states':SOURCE,'eliminant':HERE/'result.json',
                 'group_audit':HERE/'group_audit_result.json',
                 'resultant_audit':HERE/'resultant_audit_result_v2.json'}.items():
    assert sha(path)==protocol['source_sha256'][key],key
assert not (HERE/'root_probe_result_v2.json').exists()
source=json.loads(SOURCE.read_text())
producer=json.loads((HERE/'result.json').read_text())

K=PolynomialRing(GF(2),'u')
u=K.gen()
F=GF(2**41,name='u',modulus=u**41+u**3+1)
Q=PolynomialRing(F,'q')
q=Q.gen()


def dec(word):
    return F(K([(int(word)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(c)<<i for i,c in enumerate(value.polynomial().list()))


seed=dec(source['seed']<<1)
bits=[bit for bit in range(9) if bit!=5]
assert len(bits)==8


def product(mask):
    a=dec(mask<<1)
    return a*(a+seed)


basis=[product(1<<bit)**(1<<12) for bit in bits]
coefficients=[F.one()]


def eval_linearized(coefs,value):
    out=F.zero()
    for c in coefs:
        out+=c*value
        value=value*value
    return out


for v in basis:
    w=eval_linearized(coefficients,v)
    assert w
    next_coefficients=[w*coefficients[0]]
    for i in range(1,len(coefficients)):
        next_coefficients.append(coefficients[i-1]**2+w*coefficients[i])
    next_coefficients.append(coefficients[-1]**2)
    coefficients=next_coefficients
assert len(coefficients)==9

span={F.zero()}
for v in basis:
    span|={x+v for x in list(span)}
assert len(span)==256
assert all(eval_linearized(coefficients,v)==0 for v in span)

left=[]
right=[]
right_lookup={}
for i in range(71):
    mask=source['states'][1][4*i]['masks'][0]
    left.append(product(mask))
    rotated=product(source['states'][2][4*i]['masks'][0])**(1<<12)
    assert rotated in span
    assert enc(rotated) not in right_lookup
    right.append(rotated)
    right_lookup[enc(rotated)]=i
assert len(set(left))==len(set(right))==71

terms=[(degree[0],degree[1],dec(word))
       for degree,word in producer['eliminant_terms']]


def specialized(p):
    out=Q.zero()
    for i,j,c in terms:
        out+=c*(p**i)*(q**j)
    assert out and out.degree()<=4
    return out


def scan_roots(poly):
    return sorted(enc(root) for root in span if not poly(root))


def trace_split_roots(poly):
    poly=poly.monic()
    if poly.degree()==0:
        return []
    if poly.degree()==1:
        return [enc(poly[0]/poly[1])]
    for k in range(41):
        a=F.gen()**k
        x=(a*q)%poly
        tr=Q.zero()
        for _ in range(41):
            tr=(tr+x)%poly
            x=(x*x)%poly
        factor=poly.gcd(tr)
        if 0<factor.degree()<poly.degree():
            other=poly//factor
            return trace_split_roots(factor)+trace_split_roots(other)
    raise AssertionError('trace splitting failed')


def norm_roots(poly):
    x=q%poly
    remainder=Q.zero()
    for coefficient in coefficients:
        remainder=(remainder+coefficient*x)%poly
        x=(x*x)%poly
    gcd=poly.gcd(remainder)
    values=sorted(trace_split_roots(gcd))
    return values,int(gcd.degree())


orders=['scan','norm','norm','scan']
run_rows=[]
reference=None
for order in orders:
    start=time.monotonic()
    hits=[]
    roots_total=0
    gcd_degree_total=0
    for i,p in enumerate(left):
        poly=specialized(p)
        if order=='scan':
            values=scan_roots(poly)
        else:
            values,degree=norm_roots(poly)
            gcd_degree_total+=degree
        roots_total+=len(values)
        for word in values:
            j=right_lookup.get(word)
            if j is not None:
                hits.append([i,j])
    elapsed=time.monotonic()-start
    assert hits==[[61,16]]
    if reference is None:
        reference=roots_total
    else:
        assert roots_total==reference
    run_rows.append({'method':order,'elapsed_seconds':elapsed,
                     'first_codes':71,'subspace_field_roots':roots_total,
                     'valid_code_hits':hits,
                     'gcd_degree_total':gcd_degree_total if order=='norm' else None})

result={
    'status':'PASS_N41_QUARTIC_SUBSPACE_ROOT_PROBE_V2',
    'candidate_id':None,
    'right_product_subspace_rank':len(basis),
    'right_product_subspace_size':len(span),
    'linearized_coefficients':[enc(c) for c in coefficients],
    'first_code_count':len(left),
    'frozen_order':orders,
    'runs':run_rows,
    'self_maxrss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256':sha(HERE/'root_probe_protocol_v2.json'),
    'source_sha256':{'script':sha(Path(__file__)),
                     'runtime':sha(HERE/'root_probe_runtime_info_v2.json'),
                     'eliminant':sha(HERE/'result.json')},
}
(HERE/'root_probe_result_v2.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'runs':run_rows,
                  'rank':result['right_product_subspace_rank']}))
