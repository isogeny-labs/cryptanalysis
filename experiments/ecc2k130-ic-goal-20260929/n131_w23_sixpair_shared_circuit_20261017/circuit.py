"""Target-coupled W23 six-pair circuit, with matched source-inverse variants."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'n131_w18_allseed_fourpair_20261012'))
from fourpair_v2 import Algebra,Field,KaratsubaCircuit

N=131; TAPS=[0,1,2,13]; WIDTH=23; SEED_MASK=898618
ROTATIONS=[0,18,36,54,72,90]
LINKS=[(0,1,6),(2,3,7),(4,5,8),(6,7,9),(9,8,10)]
F=Field(N,TAPS)
def trace(v):
    out=0
    for _ in range(N):out^=v;v=F.square(v)
    assert out in (0,1)
    return out
def halftrace(v):
    original=v;out=0
    for _ in range((N+1)//2):out^=v;v=F.square(F.square(v))
    assert (F.square(out)^out)==original
    return out
SEED=SEED_MASK<<1
H=F.square(halftrace(SEED)); C=1^H
BITS=[i for i in range(WIDTH) if i!=SEED_MASK.bit_length()-1]
BASE=[1<<(i+1) for i in BITS]
PB=[F.square(v)^F.mul(SEED,v) for v in BASE]
TRACE=[trace(1<<i) for i in range(N)]
assert trace(SEED)==0 and C and H and len(BITS)==22

def build(target,variant):
    assert variant in ('shared','two') and target
    circ=KaratsubaCircuit(N,TAPS)
    alg=Algebra(circ,F,dense_and_threshold=3000)
    wires={'mask':[],'out':[],'source_inverse':[],'output_inverse':[],'middle':[]}
    nodes=[]
    for rot in ROTATIONS:
        masks=[circ.variable() for _ in BITS]; wires['mask'].append(masks)
        a=alg.expression(zip(masks,BASE))
        p=alg.expression(zip(masks,PB))
        circ.require_zero([circ.xor(w for w,v in zip(masks,BASE) if trace(v))])
        if variant=='shared':
            v=[circ.variable() for _ in range(N)];wires['source_inverse'].append([v])
            tensor={(i,j):circ.and_(masks[i],v[j]) for i in range(len(BITS)) for j in range(N)}
            pv=alg.expression((w,F.mul(PB[i],1<<j)) for (i,j),w in tensor.items())
            av=alg.expression((w,F.mul(BASE[i],1<<j)) for (i,j),w in tensor.items())
            circ.require_zero(alg.add(pv,alg.one).bits())
            circ.require_zero([circ.xor(w for w,t in zip(av.bits(),TRACE) if t)])
            circ.require_zero([circ.xor(w for j,w in enumerate(v) if trace(F.mul(SEED,1<<j)))])
        else:
            b=alg.add(a,alg.expression(((-1,SEED),)))
            inv=[]
            for endpoint in (a,b):
                v=[circ.variable() for _ in range(N)];inv.append(v)
                circ.require_zero(alg.add(alg.mul(endpoint,alg.from_bits(v)),alg.one).bits())
                circ.require_zero([circ.xor(w for w,t in zip(v,TRACE) if t)])
            wires['source_inverse'].append(inv)
        z=[circ.variable() for _ in range(N)];wires['out'].append(z)
        circ.clauses.append(' '.join(map(str,z))+' 0')
        zz=alg.from_bits(z)
        # C*z^2 + p*z + H = 0 is the exact fixed-seed pair output law.
        cz2=alg.expression((w,F.mul(C,basis)) for w,basis in alg.square(zz).terms)
        circ.require_zero(alg.add(cz2,alg.mul(p,zz),alg.expression(((-1,H),))).bits())
        rotated=circ.linear_element(z,[F.frob(1<<i,rot) for i in range(N)])
        nodes.append(alg.from_bits(rotated))
    for _ in range(4):
        bits=[circ.variable() for _ in range(N)];wires['middle'].append(bits)
        circ.clauses.append(' '.join(map(str,bits))+' 0')
        nodes.append(alg.from_bits(bits))
    nodes.append(alg.expression(((-1,target),)))
    for i,j,k in LINKS:
        a,b,z=nodes[i],nodes[j],nodes[k]
        ab=alg.mul(a,b); abz=alg.mul(ab,z)
        circ.require_zero(alg.add(alg.square(abz),abz,alg.square(alg.add(a,b)),alg.square(z)).bits())
    return circ,wires,{'and_gates':circ.and_count,'variables':circ.next_var-1,
                       'clauses':len(circ.clauses),'xor_rows':len(circ.xors),
                       'sparse_mul_calls':alg.sparse_mul_calls,'generic_mul_calls':alg.generic_mul_calls}
