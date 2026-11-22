"""N41 fixed-seed seven-pair direct-parity source-selector elimination."""
import importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
GEO=ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json'
V2=ROOT/'n131_w20_selector_elimination_v2_20261013'
spec=importlib.util.spec_from_file_location('w20_direct',V2/'selector.py')
w20=importlib.util.module_from_spec(spec);spec.loader.exec_module(w20)
spec=importlib.util.spec_from_file_location('n41_replay',ROOT/'n41_basis_aware_quartic_20261011/replay.py')
replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
old=w20.old
N=41
class Field(replay.Field):
    pass
F=Field()
def xor(items):
    out=0
    for x in items:out^=x
    return out
def trace(x):
    out=0
    for _ in range(N):out^=x;x=F.square(x)
    assert out in (0,1)
    return out
def frob(x,k):
    for _ in range(k):x=F.square(x)
    return x
def standard(z):return F.mul(z,F.inv(z^1))
def geometry():return json.loads(GEO.read_text())
def source_data():
    g=geometry();basis=g['blocks'][0]['basis'];seedmask=g['fixed_seed_sum_code']
    bits=[i for i in range(8) if i!=seedmask.bit_length()-1]
    wbits=[F.square(v)^v for v in basis]
    seed=xor(wbits[i] for i in range(8) if seedmask>>i&1)
    pb=[F.square(wbits[i])^F.mul(seed,wbits[i]) for i in bits]
    assert len(bits)==len(pb)==7 and seed==F.square(g['blocks'][0]['s'])^g['blocks'][0]['s']
    assert pb==[g['blocks'][0]['product_basis'][i] for i in bits]
    return g,bits,wbits,seed,pb

def projector():
    g,bits,wbits,seed,basis=source_data();rank=len(bits)
    pivots=[];rows=[]
    for p in range(N):
        row=xor((1<<j) for j,v in enumerate(basis) if v>>p&1)
        trial=rows+[row];reduced={}
        for v in trial:
            x=v
            while x:
                k=x.bit_length()-1
                if k in reduced:x^=reduced[k]
                else:reduced[k]=x;break
        if len(reduced)>len(rows):pivots.append(p);rows.append(row)
        if len(rows)==rank:break
    assert len(rows)==rank
    aug=[row|(1<<(rank+i)) for i,row in enumerate(rows)]
    for col in range(rank):
        pos=next(i for i in range(col,rank) if aug[i]>>col&1)
        aug[col],aug[pos]=aug[pos],aug[col]
        for i in range(rank):
            if i!=col and aug[i]>>col&1:aug[i]^=aug[col]
    assert [x&((1<<rank)-1) for x in aug]==[1<<i for i in range(rank)]
    invrows=[x>>rank for x in aug]
    codes=[xor((1<<j) for j,row in enumerate(invrows) if row>>i&1) for i in range(rank)]
    products=[xor(basis[j] for j in range(rank) if codes[i]>>j&1) for i in range(rank)]
    sources=[xor(wbits[bits[j]] for j in range(rank) if codes[i]>>j&1) for i in range(rank)]
    for j,v in enumerate(basis):
        assert w20.reconstruct(v,codes,pivots)==1<<j
        assert w20.reconstruct(v,products,pivots)==v
    return {'pivots':pivots,'codes':codes,'products':products,'sources':sources,
            'basis':basis,'source_bits':[wbits[i] for i in bits],
            'seed':seed,'bits':bits,'geometry':g}

def build(target):
    e=projector();g=e['geometry'];bits=e['bits'];seed=e['seed']
    circ=old.KaratsubaCircuit(N,[0,3]);alg=old.Algebra(circ,Field(),dense_and_threshold=3000)
    h2=F.square(F.halftrace(seed));coeff=1^h2
    trace_basis=[trace(1<<bit) for bit in range(N)]
    outputs=[];inverses=[];endpoints=[];rotated=[];code_vectors=[]
    for rotation in g['rotations']:
        out=[circ.variable() for _ in range(N)]
        inv=[circ.variable() for _ in range(N)]
        outputs.append(out);inverses.append(inv)
        product_columns=[F.mul(coeff,1<<i) for i in range(N)]+[F.mul(h2,1<<i) for i in range(N)]
        input_wires=out+inv
        code_columns=[w20.reconstruct(v,e['codes'],e['pivots']) for v in product_columns]
        syndrome_columns=[v^w20.reconstruct(v,e['products'],e['pivots']) for v in product_columns]
        code_wires=[circ.xor(w for w,c in zip(input_wires,code_columns) if c>>j&1)
                    for j in range(len(bits))]
        code_vectors.append(code_wires)
        allowed={sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))
                 for mask in g['permitted_canonical_a']}
        assert len(allowed)==40
        for forbidden in range(1<<len(bits)):
            if forbidden in allowed:continue
            circ.clauses.append(' '.join(
                str(-wire if forbidden>>j&1 else wire)
                for j,wire in enumerate(code_wires))+' 0')
        for q in range(N):
            circ.require_zero([circ.xor(w for w,c in zip(input_wires,syndrome_columns) if c>>q&1)])
        circ.require_zero(alg.add(alg.mul(alg.from_bits(out),alg.from_bits(inv)),alg.one).bits())
        circ.clauses.append(' '.join(map(str,out))+' 0')
        source=alg.expression((w,e['source_bits'][j]) for j,w in enumerate(code_wires))
        other=alg.add(source,alg.expression(((-1,seed),)))
        slot=[]
        for endpoint in (source,other):
            witness=[circ.variable() for _ in range(N)]
            circ.require_zero(alg.add(alg.mul(endpoint,alg.from_bits(witness)),alg.one).bits())
            circ.require_zero([circ.xor(w for w,t in zip(witness,trace_basis) if t)])
            slot.append(witness)
        endpoints.append(slot)
        images=[frob(1<<i,rotation) for i in range(N)]
        rotated.append(alg.from_bits(circ.linear_element(out,images)))
    columns={int(k):v for k,v in g['mask_columns'].items()}
    code_masks={sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits)):mask
                for mask in g['permitted_canonical_a']}
    def mismatch(wires,code):
        return [(-wire if code>>j&1 else wire) for j,wire in enumerate(wires)]
    for i in range(len(code_vectors)):
        for j in range(i+1,len(code_vectors)):
            for a_code,a in code_masks.items():
                acol={columns[a],columns[a^g['fixed_seed_sum_code']]}
                for b_code,b in code_masks.items():
                    bcol={columns[b],columns[b^g['fixed_seed_sum_code']]}
                    if acol&bcol:
                        circ.clauses.append(' '.join(map(str,
                            mismatch(code_vectors[i],a_code)+mismatch(code_vectors[j],b_code)))+' 0')
    middle=[[circ.variable() for _ in range(N)] for _ in range(5)]
    branches=[circ.variable() for _ in range(6)]
    ht_basis=[]
    for bit in range(N):
        value,image=F.square(1<<bit),0
        for _ in range((N+1)//2):image^=value;value=F.square(F.square(value))
        ht_basis.append(image)
    running=rotated[0]
    for j in range(1,7):
        upper=alg.from_bits(middle[j-1]) if j<6 else alg.expression(((-1,target),))
        total=alg.add(running,rotated[j],upper)
        ht=circ.linear_element(total.bits(),ht_basis)
        circ.require_zero(alg.add(alg.mul(alg.mul(running,rotated[j]),upper),
            alg.from_bits(ht),alg.expression(((branches[j-1],1),))).bits())
        circ.require_zero([circ.xor(w for w,t in zip(total.bits(),trace_basis) if t)])
        if j<6:circ.clauses.append(' '.join(map(str,middle[j-1]))+' 0')
        running=upper
    return circ,{'outputs':outputs,'inverses':inverses,'endpoints':endpoints,'codes':code_vectors,
                 'middle':middle,'branches':branches},e
