#!/usr/bin/env python3
"""CT164. Mod-4 Tate-lattice computation; NOT a native or PCC solve."""
import argparse
import json
from pathlib import Path

KERNELS = [
    ("factorwise", (1,4,16)), ("factorwise",(2,8,32)), ("factorwise",(3,12,48)),
    ("mixed",(5,17,42)),("mixed",(5,17,43)),("mixed",(10,21,34)),
    ("mixed",(10,23,34)),("mixed",(15,21,38)),("mixed",(15,22,37))]
M_CASES = [[[0,1],[1,1]], [[1,1],[1,0]]]

def require(condition, error):
    if not condition: raise ValueError(error)

def bits(v): return [(v >> i)&1 for i in range(6)]
def span(gens):
    out={0}
    for g in gens: out |= {g^h for h in tuple(out)}
    return out

def frob2(v):return ((v<<2)&63)|(v>>4)
def pair(a,b):return sum(((a>>(2*i)&1)*(b>>(2*i+1)&1)+(a>>(2*i+1)&1)*(b>>(2*i)&1)) for i in range(3))%2

def check_kernel(gens):
    h=span(gens)
    require(len(h)==8,"wrong kernel rank")
    require(all(pair(a,b)==0 for a in h for b in h),"kernel not isotropic")
    require({frob2(a) for a in h}==h,"kernel not Frobenius-stable")

def rank2(rows):
    pivots={}
    for v in rows:
        while v:
            p=v.bit_length()-1
            if p in pivots:v^=pivots[p]
            else:
                pivots[p]=v
                break
    return len(pivots)

def systematic_basis(kern):
    a=[bits(x) for x in kern]
    piv=[]; row=0
    for col in range(6):
        k=next((k for k in range(row,3) if a[k][col]),None)
        if k is None:continue
        a[row],a[k]=a[k],a[row]
        for i in range(3):
            if i!=row and a[i][col]:a[i]=[(u^v) for u,v in zip(a[i],a[row])]
        piv.append(col);row+=1
        if row==3:break
    require(row==3,"not a rank-3 basis")
    free=[i for i in range(6) if i not in piv]
    columns=a+[[2 if i==f else 0 for i in range(6)] for f in free]
    return columns,piv,free

def valid_m(m):
    a,b=m[0];c,d=m[1]
    return (a+d)%2==1 and (a*d-b*c)%2==1 and all(x in (0,1) for row in m for x in row)

def frob4(z,m):
    v2=z[4:6]
    return [(v2[i]+2*sum(m[i][j]*v2[j] for j in range(2)))%4 for i in range(2)]+z[:4]

def coefficients(z,cols,piv,free):
    coeff=[z[i] for i in piv]
    tail=[z[f]-sum(coeff[j]*cols[j][f] for j in range(3)) for f in free]
    require(all(t%2==0 for t in tail),"Frobenius does not preserve quotient lattice")
    return [c%2 for c in coeff]+[(t//2)%2 for t in tail]

def nullity2(gens,m):
    require(valid_m(m),"invalid source Frobenius mod-4 lift")
    check_kernel(gens)
    cols,piv,free=systematic_basis(gens)
    images=[]
    for j,v in enumerate(cols):
        z=coefficients(frob4(v,m),cols,piv,free)
        z[j]^=1
        images.append(sum(z[i]<<i for i in range(6)))
    return 6-rank2(images)

def source_guard():
    data=json.loads(Path(__file__).with_name("CT163_RESULT.json").read_text())
    require(data.get("schema")=="ct163-galois-stable-lagrangian/v1","CT163 schema")
    require(data.get("frobenius_stable_lagrangians")==9,"CT163 stable kernel count")
    require(data.get("assumption",{}).get("group_order")==11086844,"CT163 curve order")
    require(data.get("assumption",{}).get("nu12_full_two_torsion_size")==4,"CT163 full two torsion")
    obtained=[(r["kind"],tuple(r["basis"])) for r in data["kernels"]]
    require(obtained==KERNELS,"CT163 kernel binding mismatch")

def calculate():
    source_guard()
    require(223**3+1-2724==11086844,"Frobenius trace vs group order")
    require(11086844%8==4,"source requires no K-rational order-four torsion")
    valid=[]
    for a in range(2):
      for b in range(2):
       for c in range(2):
        for d in range(2):
         m=[[a,b],[c,d]]
         if valid_m(m):valid.append(m)
    require(valid==M_CASES,"Frobenius lift classification")
    results=[]
    for kind,gens in KERNELS:
        vals=[nullity2(gens,m) for m in valid]
        require(vals==[1,1],"noncyclic rational quotient 2-primary subgroup")
        results.append(dict(kind=kind,basis=list(gens),cyclic_2_sylow=True,rational_2_torsion_size_by_m=[2**x for x in vals]))
    return dict(schema="ct164-even-degree-quotient-two-torsion/v1",field=223,extension_degree=3,full_curve_order=11086844,cubic_trace=2724,m_lifts=M_CASES,kernels=results,rational_2_torsion_size=2,hyperelliptic_genus3_necessary_orbits=[[1,1,6],[2,3,3]],standing="[pcc:unverified]; mod-4 Tate module screen only")

def selftest():
    trials=[(lambda:check_kernel((1,4)),"rank"),
            (lambda:check_kernel((1,2,4)),"isotropy"),
            (lambda:check_kernel((1,4,32)),"Frobenius stability"),
            (lambda:nullity2((1,4,16),[[0,0],[0,0]]),"invalid mod-4 lift"),
            (lambda:require((11086844+4)%8==4,"bad source order"),"source 4-Sylow")]
    for f,name in trials:
        try:f()
        except ValueError:continue
        raise ValueError("negative control accepted: "+name)
    return len(trials)

def main():
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true")
    args=p.parse_args();out=calculate()
    if args.self_test:out["negative_controls_rejected"]=selftest()
    print(json.dumps(out,sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
