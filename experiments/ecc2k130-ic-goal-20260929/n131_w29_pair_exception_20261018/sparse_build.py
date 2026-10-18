"""Encode the reciprocal exception as a sparse W29-code bilinear equation."""
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

p=json.loads((here/'sparse_build_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path,digest in p['sources'].items():
    assert sha(path)==digest,path
assert not (here/'sparse_formula.xcnf').exists()
signal.signal(signal.SIGALRM,lambda _s,_f: (_ for _ in ()).throw(TimeoutError('sparse build cap')))
signal.alarm(p['wall_cap_seconds'])
started=time.monotonic()
F=design.F
H,C=design.H,design.C
CH=F.mul(C,H)
assert C^H==1
sample=json.loads(Path(p['sample']).read_text())['queries'][0]['sources']
sample=[row for row in sample if isinstance(row['code'],int)]
assert len(sample)==512


def product(code):
    out=0
    for i,basis in enumerate(design.PB):
        if code>>i&1:
            out^=basis
    return out


for i in range(32):
    a=sample[2*i]['code']
    b=sample[2*i+1]['code']
    pword,qword=product(a),product(b)
    sword=pword^qword
    old=F.mul(C,pword)^F.mul(H,qword)
    old2=F.mul(H,pword)^F.mul(C,qword)
    lhs=F.mul(old,old2)
    rhs=F.square(pword)^F.mul(pword,sword)^F.mul(CH,F.square(sword))
    assert lhs==rhs

circ=design.previous.KaratsubaCircuit(design.N,design.TAPS)
alg=design.previous.Algebra(circ,F,dense_and_threshold=3000)
pbits=[circ.variable() for _ in design.BITS]
sbits=[circ.variable() for _ in design.BITS]
circ.clauses.append(' '.join(map(str,pbits))+' 0')
circ.clauses.append(' '.join(map(str,sbits))+' 0')
qbits=[circ.xor((a,b)) for a,b in zip(pbits,sbits)]
circ.clauses.append(' '.join(map(str,qbits))+' 0')
p_expr=alg.expression(zip(pbits,design.PB))
s_expr=alg.expression(zip(sbits,design.PB))
ps=alg.mul(p_expr,s_expr)
scaled_s2=alg.expression((wire,F.mul(CH,basis))
                          for wire,basis in alg.square(s_expr).terms)
equation=alg.add(alg.square(p_expr),ps,scaled_s2,alg.one)
circ.require_zero(equation.bits())
assert alg.sparse_mul_calls==1 and alg.generic_mul_calls==0
circ.write(here/'sparse_formula.xcnf')
finished=time.monotonic()
signal.alarm(0)
out={'status':'PASS_N131_W29_SPARSE_EXCEPTION_CIRCUIT',
     'candidate_id':None,'curve_id':p['curve_id'],
     'source_code_bits_per_pair':28,'sparse_pair_products':alg.sparse_pair_products,
     'equation':'p^2+p*s+C*H*s^2=1; p,s,p+s are nonzero W29 products',
     'sampled_algebra_identities':32,
     'and_gates':circ.and_count,'variables':circ.next_var-1,
     'clauses':len(circ.clauses),'native_xor_rows':len(circ.xors),
     'formula_bytes':(here/'sparse_formula.xcnf').stat().st_size,
     'formula_sha256':sha(here/'sparse_formula.xcnf'),
     'protocol_sha256':sha(here/'sparse_build_protocol.json'),
     'wall_seconds':finished-started,
     'self_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(here/'sparse_build_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps({key:out[key] for key in ('status','sparse_pair_products',
                                           'and_gates','variables','clauses',
                                           'native_xor_rows','formula_bytes')}))
