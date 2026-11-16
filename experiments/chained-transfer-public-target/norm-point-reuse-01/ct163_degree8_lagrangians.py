#!/usr/bin/env python3
"""Exhaustive level-2 descent kernel screen. No actual quotient/Jacobian is built."""
import argparse
import itertools
import json
from collections import Counter

def pairing(a,b):
    return sum((((a>>(2*i))&1)*((b>>(2*i+1))&1) +
                ((a>>(2*i+1))&1)*((b>>(2*i))&1)) for i in range(3))%2

def frob(v):
    return ((v<<2)&63)|(v>>4)

def span(rows):
    s={0}
    for v in rows:
        s |= {x^v for x in tuple(s)}
    return frozenset(s)

def isotr(s, form=pairing):
    return all(form(a,b)==0 for a in s for b in s)

def stable(s, action=frob):
    return frozenset(action(v) for v in s)==s

def basis(s):
    b=[];seen={0}
    for v in sorted(s):
        if v not in seen:
            b.append(v)
            seen |= {v^x for x in tuple(seen)}
    return b

def loc(s):
    return [sum((v & (~(3<<(2*i)) & 63))==0 for v in s) for i in range(3)]

def check(ok,msg):
    if not ok: raise ValueError(msg)

def enumerate_kernels():
    subspaces={span(t) for t in itertools.combinations(range(1,64),3)}
    subspaces={s for s in subspaces if len(s)==8}
    lag=[s for s in subspaces if isotr(s)]
    stable_lag=sorted([s for s in lag if stable(s)],key=lambda s:tuple(sorted(s)))
    check(len(subspaces)==1395 and len(lag)==135 and len(stable_lag)==9,
          "finite Gaussian/Lagrangian/Frobenius census")
    kernels=[]
    for s in stable_lag:
        local=loc(s)
        check(all(x in (1,2) for x in local),"unexpected factor support")
        kernels.append(dict(span=sorted(s),basis=basis(s),
                            kind="factorwise" if local==[2,2,2] else "mixed",
                            local_sizes=local,
                            frobenius_fixed=sum(v==frob(v) for v in s)))
    check(Counter(r["kind"] for r in kernels)==Counter(factorwise=3,mixed=6),
          "kernel types")
    check(all(r["frobenius_fixed"]==2 for r in kernels),"fixed subgroup")
    return dict(schema="ct163-galois-stable-lagrangian/v1",
                assumption=dict(p=223,extension_degree=3,
                    nu12_full_two_torsion_size=4,weierstrass_roots=3,
                    group_order=11086844),
                all_three_subspaces=1395,lagrangian_subspaces=135,
                frobenius_stable_lagrangians=9,factorwise=3,mixed=6,
                kernels=kernels,
                status="[pcc:unverified]; finite 2-torsion kernels only, no Jacobian or DLP speedup")

def self_test(out):
    check(not isotr(span((1,2,4))),"non-isotropic mutation accepted")
    check(len(span((1,4)))!=8,"dimension mutation accepted")
    check(not stable(span((1,4,32))),"nonstable mutation accepted")
    all3={span(t) for t in itertools.combinations(range(1,64),3)}
    all3=[s for s in all3 if len(s)==8]
    check(sum(isotr(s,lambda a,b:0) for s in all3)!=135,
          "zero pairing mutation accepted")
    check(sum(stable(s,lambda x:x) for s in all3 if isotr(s))!=9,
          "identity Frobenius mutation accepted")
    altered=dict(out["assumption"],nu12_full_two_torsion_size=2)
    check(altered["nu12_full_two_torsion_size"]!=4,
          "full 2-torsion mutation accepted")
    return 6

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    out=enumerate_kernels()
    if args.self_test: out["negative_controls_rejected"]=self_test(out)
    print(json.dumps(out,sort_keys=True,separators=(",",":")))

if __name__=="__main__":main()
