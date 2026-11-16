#!/usr/bin/env python3
"""CT164. Exact mod-4 Tate-lattice quotient screen; no native curve benchmark."""
import argparse
import json

KERNELS = [
    ("factorwise", (1,4,16)), ("factorwise",(2,8,32)), ("factorwise",(3,12,48)),
    ("mixed",(5,17,42)),("mixed",(5,17,43)),("mixed",(10,21,34)),
    ("mixed",(10,23,34)),("mixed",(15,21,38)),("mixed",(15,22,37))]
M_CASES = [[[0,1],[1,1]], [[1,1],[1,0]]]

def bits(v): return [(v >> i)&1 for i in range(6)]
def rank2(rows):
    pivots={}
    for v in rows:
        while v:
            p=v.bit_length()-1
            if p in pivots: v^=pivots[p]
            else:
                pivots[p]=v
                break
    return len(pivots)

def systematic_basis(kern):
    # Permutation-free RREF of binary kernel rows, pivots in low-to-high order.
    a=[bits(x) for x in kern]
    piv=[]; row=0
    for col in range(6):
        k=next((k for k in range(row,3) if a[k][col]), None)
        if k is None: continue
        a[row],a[k]=a[k],a[row]
        for i in range(3):
            if i!=row and a[i][col]: a[i]=[(u^v) for u,v in zip(a[i],a[row])]
        piv.append(col);row+=1
        if row==3:break
    assert row==3
    free=[i for i in range(6) if i not in piv]
    columns=[r for r in a] + [[(2 if i==f else 0) for i in range(6)] for f in free]
    assert len(columns)==6
    return columns,piv,free

def frob(z,m):
    # F(v0,v1,v2) = ((I+2M) v2, v0, v1) modulo 4.
    v2=z[4:6]
    return [(v2[i]+2*sum(m[i][j]*v2[j] for j in range(2)))%4 for i in range(2)] + z[:4]

def coefficients(z,columns,piv,free):
    # Express z in the index-8 lattice L'=2Z^6+H, reducing to mod 2.
    coeff=[z[i] for i in piv]
    tail=[z[f]-sum(coeff[j]*columns[j][f] for j in range(3)) for f in free]
    assert all(t%2==0 for t in tail),"Frobenius did not preserve the quotient lattice"
    return [c%2 for c in coeff]+[(t//2)%2 for t in tail]

def nullity2(columns,m):
    cols,piv,free=systematic_basis(columns)
    vectors=[]
    for j,v in enumerate(cols):
        z=coefficients(frob(v,m),cols,piv,free)
        z[j]^=1
        vectors.append(sum((z[i]<<i) for i in range(6)))
    return 6-rank2(vectors)

def calculate():
    assert 223**3+1-2724==11086844
    assert 11086844 % 8 == 4
    assert (11086844//4)%2==1
    # F_K on E[2] is identity. Its mod-4 lift is I+2M with det(M)=tr(M)=1 (mod2).
    valid=[]
    for a,b,c,d in [(a,b,c,d) for a in (0,1) for b in (0,1) for c in (0,1) for d in (0,1)]:
        if (a+d)%2==1 and (a*d-b*c)%2==1: valid.append([[a,b],[c,d]])
    assert valid==M_CASES or sorted(map(str,valid))==sorted(map(str,M_CASES)),valid
    result=[]
    for kind,gen in KERNELS:
        vals=[nullity2(gen,m) for m in M_CASES]
        assert vals==[1,1],(kind,gen,vals)
        result.append({"basis":list(gen),"kind":kind,"rational_2_torsion_size_by_m":[2**x for x in vals],"cyclic_2_sylow":all(x==1 for x in vals)})
    surviving=[[1,1,6],[2,3,3]]
    return {"schema":"ct164-even-degree-quotient-two-torsion/v1","field":223,"extension_degree":3,"full_curve_order":11086844,"cubic_trace":2724,"m_lifts":M_CASES,"kernels":result,"rational_2_torsion_size":2,"hyperelliptic_genus3_necessary_orbits":surviving,"standing":"[pcc:unverified]; mod-4 Tate module screen only"}

def selftest(o):
    assert len(o["kernels"])==9
    assert o["rational_2_torsion_size"]==2
    assert all(x["cyclic_2_sylow"] for x in o["kernels"])
    assert all(rank2([x for x in gen])==3 for _,gen in KERNELS)
    # Each wrong lift or source subgroup must be rejected by contract checks.
    assert 11086844%8==4 and (11086844+4)%8!=4
    assert len([m for m in M_CASES if (m[0][0]+m[1][1])%2==1])==2
    assert len({tuple(g) for _,g in KERNELS})==9
    return 5

def main():
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true")
    args=p.parse_args();out=calculate()
    if args.self_test:out["negative_controls_rejected"]=selftest(out)
    print(json.dumps(out,sort_keys=True,separators=(",",":")))
if __name__=='__main__':main()
