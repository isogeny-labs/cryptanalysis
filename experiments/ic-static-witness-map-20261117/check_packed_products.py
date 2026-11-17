#!/usr/bin/env python3
"""Exact polynomial-window model for a proposed two-products-per-PCLMUL path."""
import hashlib, json, random
from pathlib import Path
P = Path(__file__).resolve().parent
def clmul(a,b):
    out=0
    while b:
        bit=b & -b; out ^= a << (bit.bit_length()-1); b ^= bit
    return out
def reference(values):
    a0,a1,b0,b1=values
    return clmul(a0,b0),clmul(a1,b1)
def gap(n): return 32 if n<=16 else 2*n
def packed(values,n,mutant=None):
    a0,a1,b0,b1=values; g=gap(n)
    if mutant=='overlapping_gap': g=2*n-2
    a=a0 | (a1<<g); b=b0 | (b1<<g)
    product=a*b if mutant=='integer_product' else clmul(a,b)
    low=product if mutant=='missing_low_mask' else product & ((1<<(2*n-1))-1)
    high=(product >> (2*g-(mutant=='wrong_high_window'))) & ((1<<(2*n-1))-1)
    return low,high
rows=[]; mutants={k:None for k in ['overlapping_gap','integer_product','missing_low_mask','wrong_high_window']}
rng=random.Random(20261117)
for n in range(1,22):
    g=gap(n); assert g>=2*n-1 and g+n<=64 and 2*g+2*n-2<128
    basis=[]
    for i in range(2*n):
        for j in range(2*n):
            v=[0,0,0,0]; v[i//n]=1<<(i%n); v[2+j//n]=1<<(j%n); basis.append(tuple(v))
    edge=[0,1,1<<(n-1),(1<<n)-1]
    edges=[(a,b,c,d) for a in edge for b in edge for c in edge for d in edge]
    randoms=[tuple(rng.randrange(1<<n) for _ in range(4)) for _ in range(4096)] if n in [15,18,21] else []
    for v in basis+edges+randoms:
        exact=reference(v); assert packed(v,n)==exact,(n,v)
        for name,witness in mutants.items():
            if witness is None and n>=2 and packed(v,n,name)!=exact:
                mutants[name]=dict(n=n,values=v,exact=exact,mutant=packed(v,n,name))
    rows.append(dict(n=n,gap=g,basis_pairs=len(basis),edge_tuples=len(edges),random_tuples=len(randoms)))
assert all(mutants.values())
assert 3*22-1>64  # Even the minimum non-overlapping gap cannot fit n22.
out=dict(status='pass',standing='unsigned exact-integer model only; no native implementation or timing',scope='canonical polynomial elements n1..21; two independent raw carry-less products extracted exactly; no approximation or integer carry argument',basis_argument='Packing, carry-less multiplication and window extraction are F2-bilinear in the two packed input vectors. Equality on all (2n)^2 monomial basis pairs proves equality on all canonical inputs. Cross-term support G..G+2n-2 misses windows0..2n-2 and2G..2G+2n-2 when G>=2n-1. Packed operand degree G+n-1 must be below64.',rows=rows,mutants=mutants,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seed=20261117)
path=P/'packed-product-model.json'; assert not path.exists()
path.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(status='pass',basis_pairs=sum(r['basis_pairs'] for r in rows),edge_tuples=sum(r['edge_tuples'] for r in rows),random_tuples=sum(r['random_tuples'] for r in rows),mutants_rejected=len(mutants))))
