"""Encode a full-W29 necessary condition for reciprocal pair outputs."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
sys.path.insert(0,str(root/'n41_n131_fivepair_w9_w29_20261017'))
import circuit_n131_3p2 as design

p=json.loads((here/'build_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path,digest in p['sources'].items():
    assert sha(path)==digest,path
assert not (here/'formula.xcnf').exists()
signal.signal(signal.SIGALRM,lambda _s,_f: (_ for _ in ()).throw(TimeoutError('build wall cap')))
signal.alarm(p['wall_cap_seconds'])
started=time.monotonic()
assert design.N==131 and len(design.BITS)==28
assert design.ROTATIONS==[0,18,36,54,72]
F=design.F
H,C=design.H,design.C
assert C^H==1
basis={}
for word in design.PB:
    value=word
    while value:
        pivot=value.bit_length()-1
        if pivot not in basis:
            basis[pivot]=value
            break
        value^=basis[pivot]
assert len(basis)==28
sample=json.loads(Path(p['sample']).read_text())['queries'][0]['sources']
sample=[row for row in sample if isinstance(row['code'],int)]
assert len(sample)==512
for row in sample:
    product=0
    for bit,value in enumerate(design.PB):
        if row['code']>>bit&1:
            product^=value
    assert product==row['p']
    for root_word in row['pair_roots']:
        assert F.mul(C,F.square(root_word))^F.mul(product,root_word)^H==0

circ=design.previous.KaratsubaCircuit(design.N,design.TAPS)
alg=design.previous.Algebra(circ,F,dense_and_threshold=3000)
bits0=[circ.variable() for _ in design.BITS]
bits1=[circ.variable() for _ in design.BITS]
circ.clauses.append(' '.join(map(str,bits0))+' 0')
circ.clauses.append(' '.join(map(str,bits1))+' 0')
differences=[circ.xor((a,b)) for a,b in zip(bits0,bits1)]
circ.clauses.append(' '.join(map(str,differences))+' 0')


def linear(bits,coeff):
    return alg.expression((wire,F.mul(coeff,basis))
                          for wire,basis in zip(bits,design.PB))


u=alg.add(linear(bits0,C),linear(bits1,H))
v=alg.add(linear(bits0,H),linear(bits1,C))
uv=alg.mul(u,v)
circ.require_zero(alg.add(uv,alg.one).bits())
circ.write(here/'formula.xcnf')
finished=time.monotonic()
signal.alarm(0)
out={'status':'PASS_N131_W29_RECIPROCAL_EXCEPTION_NECESSARY_CIRCUIT',
     'candidate_id':None,'curve_id':p['curve_id'],
     'source_code_bits_per_pair':28,'source_product_basis_rank':28,
     'source_sample_codes_checked':len(sample),
     'equation':'(C*p+H*q)*(H*p+C*q)=1; p,q are distinct nonzero W29 products',
     'and_gates':circ.and_count,'variables':circ.next_var-1,
     'clauses':len(circ.clauses),'native_xor_rows':len(circ.xors),
     'formula_bytes':(here/'formula.xcnf').stat().st_size,
     'formula_sha256':sha(here/'formula.xcnf'),
     'protocol_sha256':sha(here/'build_protocol.json'),
     'wall_seconds':finished-started,
     'self_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(here/'build_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps({key:out[key] for key in ('status','and_gates','variables',
                                           'clauses','native_xor_rows','formula_bytes',
                                           'wall_seconds')}))
