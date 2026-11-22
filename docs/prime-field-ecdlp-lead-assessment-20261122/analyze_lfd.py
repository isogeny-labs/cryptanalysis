import json, collections
ROWS="experiments/ic-solving-degree/rows-merged.jsonl"
data=collections.defaultdict(list)
for line in open(ROWS):
    line=line.strip()
    if not line: continue
    d=json.loads(line)
    fam,m,k,lfd=d.get("family"),d.get("m"),d.get("k"),d.get("lfd")
    if None in (fam,m,k,lfd): continue
    data[(fam,m)].append((k,lfd))

def fit_slope(ks, yk):
    xs=ks; ys=[yk[k] for k in ks]; n=len(xs)
    if n<2 or len(set(xs))<2: return None,None
    mx=sum(xs)/n; my=sum(ys)/n
    sxx=sum((x-mx)**2 for x in xs); sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    s=sxy/sxx; return s, my-s*mx

def sse(ks,yk,law): return sum((yk[k]-law(k))**2 for k in ks)

print("MEASURED last-fall/solving degree (LFD = Caminata-Gorla solving degree) vs tower height k")
print("repo k = tower height t ; m = arity ; factor base = mu_{2^k}, so N=|V|=2^k.")
print("Source: experiments/ic-solving-degree/rows-merged.jsonl  [pcc:unverified]\n")
print(f"{'m':>2} {'k-range':>8} {'LFD values':>24} {'slope dLFD/dk':>13}  {'best law':>12}  verdict")
print("-"*96)
laws={"const":lambda k:7, "k+2":lambda k:k+2, "P4~k/4":lambda k:(k+14)//4+3, "mk+1":None}
for fam in ("prime","binary"):
    print(f"==== family={fam} ====")
    for m in range(2,9):
        pts=data.get((fam,m),[])
        if not pts: continue
        byk=collections.defaultdict(list)
        for k,lfd in pts: byk[k].append(lfd)
        ks=sorted(byk); yk={k:max(byk[k]) for k in ks}
        slope,_=fit_slope(ks,yk)
        L={name:(fn if fn else (lambda k,m=m:m*k+1)) for name,fn in laws.items()}
        errs={name:sse(ks,yk,fn) for name,fn in L.items()}
        best=min(errs,key=errs.get)
        vals=",".join(str(yk[k]) for k in ks)
        if slope is None: verdict="(single k)"
        elif slope<0.5: verdict="BOUNDED/SUBLINEAR -> oracle polylog-ish; exponent OPEN"
        elif best=="mk+1" or slope>=m-0.5: verdict="LINEAR, saturates mk+1 -> cost ~C(mk,mk)^w; B1 DEAD"
        else: verdict="linear -> likely >=1/2"
        sl = f"{slope:.2f}" if slope is not None else " - "
        print(f"{m:>2} {str(min(ks))+'..'+str(max(ks)):>8} {vals:>24} {sl:>13}  {best:>12}  {verdict}")
    print()
print("""EXPONENT IMPLICATION (factor base N=2^k, balanced N~p^{1/m} => k ~ (log2 p)/m, #vars ~ mk ~ log2 p):
  * LFD bounded (O(1) in k): #monomials ~ (mk)^O(1) = polylog(p) => per-decomposition oracle is
    poly(log p) => sub-sqrt(p) exponent possible.  SEEN ONLY at m=3 (LFD flat ~7).
  * LFD = mk+1 (linear, slope~m): D ~ mk ~ log2 p => #monomials ~ C(2mk,mk) ~ p^2 => oracle cost
    >> p^{1/2}.  SEEN at every arity m>=5 that B1 actually needs for a sub-sqrt exponent.
  => The ONE arity with a bounded-degree oracle (m=3) is exactly the one that cannot beat sqrt(p)
     (needs m>=5); the arities that could (m>=5) have solving degree pinned to the mk+1 cap.
     On this measured evidence the PKM two-power-subgroup tower does NOT yield the p-independent
     decomposition oracle a sub-sqrt(p) exponent requires: B1 DEAD AS POSED (M2's 70% branch).
  CAVEAT: high-m lever is short (k<=4); rigorous step = feed LFD=mk+1 into experiments/ic-costmodel
  and confirm the crossover p* does not exist below cryptographic sizes.""")
