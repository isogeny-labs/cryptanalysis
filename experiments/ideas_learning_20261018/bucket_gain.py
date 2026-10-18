#!/usr/bin/env python3
"""Exact level-one subgroup bucket statistic, with matched SHA null."""
import hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from prefilter_search import curve,point,scalar_mul,INF
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
def fwht(a):
    a=a.copy();h=1
    while h<len(a):
        for i in range(0,len(a),h*2):
            x=a[i:i+h].copy();y=a[i+h:i+2*h].copy()
            a[i:i+h]=x+y;a[i+h:i+2*h]=x-y
        h*=2
    return a
def gain(hv,M,direct=False):
    N=len(hv);hv=np.array(hv,dtype=int);used=len(set(hv.tolist()))
    ind=np.array([hv==i for i in range(M)],dtype=float)
    A=np.fft.rfft(ind,axis=1)
    W=np.fft.irfft(fwht(fwht(A)**2)/M,n=N,axis=1).real
    err=float(np.max(np.abs(W-np.rint(W))))
    assert err<1e-6
    W=np.rint(W).astype(np.int64)
    assert W.min()>=0 and int(W.sum())==N*N
    num=np.stack([W[:,hv==c].sum(axis=1) for c in range(M)],axis=1)
    den=W.sum(axis=1)
    if direct:
        exact=np.zeros((M,M),dtype=np.int64)
        for q in range(N):
            for r in range(N):exact[hv[q]^hv[r],hv[(q+r)%N]]+=1
        assert np.array_equal(num,exact)
    ratios=np.divide(num,den[:,None],out=np.zeros_like(num,dtype=float),where=den[:,None]>0)
    s,c=np.unravel_index(np.argmax(ratios),ratios.shape)
    return {"nominal_M":M,"effective_M":used,"gain_effective":used*float(ratios[s,c]),"gain_nominal":M*float(ratios[s,c]),"max_pi":float(ratios[s,c]),"s":int(s),"c":int(c),"offset_xor":int(s^c),"numerator":int(num[s,c]),"denominator":int(den[s]),"ordered_pairs":N*N,"direct_pair_check":direct,"maximum_fft_rounding_residual":err,"bucket_counts":np.bincount(hv,minlength=M).tolist(),"numerators":num.tolist(),"denominators":den.tolist()}
def main():
    if (HERE/"bucket-results.json").exists():raise SystemExit("Append-only run already exists")
    proto=json.loads((HERE/"BUCKET-PROTOCOL.json").read_text())
    save("bucket-launch.json",{"argv":sys.argv,"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"source_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/"BUCKET-PROTOCOL.json",HERE/"BUCKET-AMENDMENT-01.json",HERE/"prefilter_search.py"]},"gpu":{"devices":[]},"scope":"CPU-only exact toy enumeration control"})
    results=[];inputs=[];t=time.process_time()
    for cc in proto["curves"]:
        E,sub,full,rec=curve(cc["n"],cc["b"]);N=len(sub)
        inputs.append({"curve":rec,"subgroup_points":[point(P) for P in sub]})
        filters=[("halving-trace",[0 if P.inf else E.F.trace(P.x) for P in sub],2)]
        for j in [1,2,3,4]:
            for offset in [1,2]:
                alpha=[E.F.pow(2,i+offset) for i in range(j)]
                hv=[0 if P.inf else sum(E.F.trace(E.F.mul(a,P.x))<<i for i,a in enumerate(alpha)) for P in sub]
                filters.append((f"trace-offset{offset}-j{j}",hv,1<<j))
        for name,hv,M in filters:
            g=gain(hv,M,direct=N<=100)
            # SHA null encodes x, so Q and -Q remain indistinguishable as required.
            Me=g["effective_M"]
            keys=[str(P.x) if not P.inf else "INF" for P in sub]
            unique=sorted(set(keys),key=lambda x:hashlib.sha256(f"x-only-null-20261018|{x}".encode()).digest())
            used=sorted(set(hv));mapping={key:used[k%Me] for k,key in enumerate(unique)}
            null=[mapping[key] for key in keys]
            ng=gain(null,M,direct=N<=100)
            assert ng["effective_M"]==Me
            results.append({"domain":"prime-order subgroup including identity","curve_id":rec["curve_id"],"n":cc["n"],"r":N,"filter":name,"statistic":g,"matched_sha_null":ng})
        # Group C_(4r) positive controls have a verified order-4 torsion generator.
        assert rec["curve"]["cofactor"]==4
        T=next(T for P in full if not (T:=scalar_mul(E,P,N)).inf and scalar_mul(E,T,2)!=INF)
        H=E.add(sub[1],T)
        cyc=[INF]
        for _ in range(1,4*N):cyc.append(E.add(cyc[-1],H))
        assert len(set(cyc))==4*N and E.add(cyc[-1],H)==INF
        trace=[0 if P.inf else E.F.trace(P.x) for P in cyc]
        assert all(v==(k%2) for k,v in enumerate(trace))
        for name,hv,M in [("full-group-halving-trace",trace,2),("full-group-point-quotient4-instrument",[k%4 for k in range(4*N)],4)]:
            g=gain(hv,M,direct=len(cyc)<=200)
            assert abs(g["gain_effective"]-M)<1e-9
            results.append({"domain":"full curve group","curve_id":rec["curve_id"],"n":cc["n"],"group_order":4*N,"filter":name,"statistic":g,"efficient_x_only_candidate":name=="full-group-halving-trace"})
    save("bucket-inputs.json",inputs)
    save("bucket-results.json",{"rows":results,"cpu_seconds":time.process_time()-t,"scope":"exact toy single-bucket statistic at level1; no asymptotic conclusion","all_fft_totals_checked":True})
    print(json.dumps([{k:r[k] for k in ["domain","curve_id","filter"]}|{"gain":r["statistic"]["gain_effective"],"null_gain":r.get("matched_sha_null",{}).get("gain_effective")} for r in results]))
if __name__=="__main__":main()
