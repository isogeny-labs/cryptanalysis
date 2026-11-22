"""Exact fixed-seed four-pair target circuit on the N41 public point."""
import sys
from pathlib import Path

ROOT=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
sys.path.insert(0,str(ROOT/'n131_w18_allseed_fourpair_20261012'))
from fourpair_v2 import Algebra,Field,KaratsubaCircuit

N=41;TAPS=[0,3];WIDTH=11;SEED_MASK=56
ROTATIONS=[0,12,24,36]
LINKS=[(0,1,4),(2,3,5),(4,5,6)]
F=Field(N,TAPS)
SEED=SEED_MASK<<1
BITS=[i for i in range(WIDTH) if i!=SEED_MASK.bit_length()-1]
BASE=[1<<(i+1) for i in BITS]
PB=[F.square(v)^F.mul(SEED,v) for v in BASE]

def trace(v):
    out=0
    for _ in range(N):out^=v;v=F.square(v)
    assert out in (0,1)
    return out

def halftrace(v):
    original=v;out=0
    for _ in range((N+1)//2):out^=v;v=F.square(F.square(v))
    assert F.square(out)^out==original
    return out

H=F.square(halftrace(SEED));C=1^H
TRACE=[trace(1<<i) for i in range(N)]
assert len(BITS)==10 and trace(SEED)==0 and H and C

def source_columns(source_input):
    mapping={}
    for line in Path(source_input).read_text().splitlines():
        p=line.split()
        if p and p[0]=='S' and int(p[1])==0:
            code=int(p[3]);columns=(int(p[7]),int(p[8]))
            if code in mapping:assert mapping[code]==columns
            mapping[code]=columns
    assert len(mapping)==281
    return mapping

def build(target_reciprocals,source_input):
    assert len(target_reciprocals)==41 and all(target_reciprocals)
    assert len(set(target_reciprocals))==41
    circ=KaratsubaCircuit(N,TAPS)
    alg=Algebra(circ,F,dense_and_threshold=3000)
    wires={'mask':[],'out':[],'source_inverse':[],'middle':[],'selector':[]}
    nodes=[]
    for rotation in ROTATIONS:
        masks=[circ.variable() for _ in BITS];wires['mask'].append(masks)
        a=alg.expression(zip(masks,BASE))
        p=alg.expression(zip(masks,PB))
        circ.require_zero([circ.xor(w for w,v in zip(masks,BASE) if trace(v))])
        v=[circ.variable() for _ in range(N)];wires['source_inverse'].append(v)
        tensor={(i,j):circ.and_(masks[i],v[j]) for i in range(len(BITS)) for j in range(N)}
        pv=alg.expression((w,F.mul(PB[i],1<<j)) for (i,j),w in tensor.items())
        av=alg.expression((w,F.mul(BASE[i],1<<j)) for (i,j),w in tensor.items())
        circ.require_zero(alg.add(pv,alg.one).bits())
        circ.require_zero([circ.xor(w for w,t in zip(av.bits(),TRACE) if t)])
        circ.require_zero([circ.xor(w for j,w in enumerate(v) if trace(F.mul(SEED,1<<j)))])
        z=[circ.variable() for _ in range(N)];wires['out'].append(z)
        circ.clauses.append(' '.join(map(str,z))+' 0')
        zz=alg.from_bits(z)
        cz2=alg.expression((w,F.mul(C,basis)) for w,basis in alg.square(zz).terms)
        circ.require_zero(alg.add(cz2,alg.mul(p,zz),alg.expression(((-1,H),))).bits())
        rotated=circ.linear_element(z,[F.frob(1<<i,rotation) for i in range(N)])
        nodes.append(alg.from_bits(rotated))
    for _ in range(2):
        bits=[circ.variable() for _ in range(N)];wires['middle'].append(bits)
        circ.clauses.append(' '.join(map(str,bits))+' 0')
        nodes.append(alg.from_bits(bits))
    selector=[circ.variable() for _ in range(6)]
    wires['selector']=selector
    choices=[]
    for k in range(41):
        predicate=-1
        for j,wire in enumerate(selector):
            literal=wire if k>>j&1 else circ.xor((wire,-1))
            predicate=circ.and_(predicate,literal)
        choices.append(predicate)
    circ.clauses.append(' '.join(map(str,choices))+' 0')
    target_bits=circ.linear_element(choices,target_reciprocals)
    nodes.append(alg.from_bits(target_bits))
    for i,j,k in LINKS:
        a,b,z=nodes[i],nodes[j],nodes[k]
        ab=alg.mul(a,b);abz=alg.mul(ab,z)
        circ.require_zero(alg.add(alg.square(abz),abz,alg.square(alg.add(a,b)),alg.square(z)).bits())
    columns=source_columns(source_input)
    forbidden={(a,b) for a,ca in columns.items() for b,cb in columns.items()
               if a<=b and (a==b or not set(ca).isdisjoint(cb))}
    for slot in range(4):
        for other in range(slot+1,4):
            # Code equality is forbidden for every assignment, even when the
            # shared source law already makes a particular code impossible.
            different=[circ.xor((a,b)) for a,b in zip(wires['mask'][slot],wires['mask'][other])]
            circ.clauses.append(' '.join(map(str,different))+' 0')
            for a,b in forbidden:
                if a==b:continue
                for x,y in ((a,b),(b,a)):
                    clause=[-wire if x>>bit&1 else wire for bit,wire in enumerate(wires['mask'][slot])]
                    clause.extend(-wire if y>>bit&1 else wire for bit,wire in enumerate(wires['mask'][other]))
                    circ.clauses.append(' '.join(map(str,clause))+' 0')
    counts={'variables':circ.next_var-1,'and_gates':circ.and_count,
            'clauses':len(circ.clauses),'xor_rows':len(circ.xors),
            'forbidden_code_pairs':len(forbidden)}
    return circ,wires,counts
