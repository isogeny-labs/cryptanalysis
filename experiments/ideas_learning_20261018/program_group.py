#!/usr/bin/env python3
"""Restricted program search in actual group-law query kernels, without target logs."""
import bisect,hashlib,itertools,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from prefilter_search import curve,point,digest,INF
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
def key(P):return (P.x,P.y,P.inf)
def projected_base(E,sub,rec,ell,mult):
    h=rec["curve"]["cofactor"];adds=0;fb=set();pre=[]
    for x in range(1<<ell):
        P=E.lift_x(E.F.mul(mult,x))
        if P is None:continue
        ps=[P] if E.neg(P)==P else [P,E.neg(P)]
        for P in ps:
            pre.append(P);Q=INF;T=P;k=h
            while k:
                if k&1:Q=E.add(Q,T);adds+=1
                T=E.add(T,T);adds+=1;k>>=1
            if not Q.inf:fb.add(Q)
    fb=sorted(fb,key=key)
    assert set(fb).issubset(set(sub))
    return fb,{"projection_group_additions":adds,"preprojection_points":[point(P) for P in pre],"projected_points":[point(P) for P in fb]}
def truth(E,sub,fb):
    dlog={P:k for k,P in enumerate(sub)};logs=[dlog[P] for P in fb];r=len(sub);wit={};mults=[0]*r
    for a,b,c in itertools.product(logs,repeat=3):
        k=(a+b+c)%r;wit.setdefault(k,[a,b,c]);mults[k]+=1
    for k,abc in wit.items():assert E.sum([sub[a] for a in abc])==sub[k]
    return [int(v>0) for v in mults[1:]],{"ordered_tuples":sum(mults),"support_nonidentity":sum(v>0 for v in mults[1:]),"multiplicity":mults,"witnesses":wit}
def kernel(E,fb,targets,name):
    adds=probes=compares=setupadd=setupprobe=sortbound=0;table=None;start=time.process_time()
    if name!="ordered-exhaustive-group":
        table=[]
        for P,Q in itertools.product(fb,repeat=2):table.append(key(E.add(P,Q)));setupadd+=1
        if name=="pair-hash-group":setupprobe=len(table);table=set(table)
        else:sortbound=len(table)*max(0,(len(table)-1).bit_length());table=sorted(set(table))
    setupsec=time.process_time()-start;start=time.process_time();out=[]
    for R in targets:
        found=False
        if name=="ordered-exhaustive-group":
            for P,Q,T in itertools.product(fb,repeat=3):
                S=E.add(E.add(P,Q),T);adds+=2;compares+=1
                if S==R:found=True;break
        else:
            for P in fb:
                q=key(E.add(R,E.neg(P)));adds+=1
                if name=="pair-hash-group":probes+=1;found=q in table
                else:
                    lo,hi=0,len(table)
                    while lo<hi:
                        mid=(lo+hi)//2;compares+=1
                        if table[mid]<q:lo=mid+1
                        else:hi=mid
                    compares+=1;found=lo<len(table) and table[lo]==q
                if found:break
        out.append(int(found))
    counts={"pair_setup_group_additions":setupadd,"pair_setup_hash_probes":setupprobe,"sort_comparison_upper_bound":sortbound,"online_group_additions":adds,"online_hash_probes":probes,"online_comparisons":compares}
    return out,{"kernel":name,"counts":counts,"unit_weight_work":sum(counts.values()),"setup_cpu_seconds":setupsec,"online_cpu_seconds":time.process_time()-start}
def main():
    if (HERE/"program-group-results.json").exists():raise SystemExit("Append-only run exists")
    p=json.loads((HERE/"PROGRAM-02-PROTOCOL.json").read_text())
    p["training"]["ell"]=4;p["heldout"]["ell"]=4
    save("program-group-launch.json",{"argv":sys.argv,"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"sources":{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in [Path(__file__),HERE/"prefilter_search.py",HERE/"PROGRAM-02-PROTOCOL.json",HERE/"PROGRAM-02-AMENDMENT-01.json"]},"gpu":{"devices":[]},"scope":"CPU-only toy correctness/stage control"})
    rows=[];inputs=[];selected=None;t=time.process_time()
    for phase in ["training","heldout"]:
        cc=p[phase];start=time.process_time()
        try:E,sub,full,rec=curve(cc["n"],cc["b"])
        except ValueError as exc:
            save("program-group-results.json",{"rows":rows,"admission_failure":json.loads(str(exc)),"phase":phase,"selected":selected});return
        curve_setup=time.process_time()-start
        candidates=itertools.product(p["multipliers"],p["kernel_grammar"])
        if phase=="heldout":candidates=[(selected["multiplier"],selected["kernel"]),(1,"pair-hash-group")]
        for mult,name in candidates:
            start=time.process_time();fb,base=projected_base(E,sub,rec,cc["ell"],mult);basesec=time.process_time()-start
            start=time.process_time();labels,cert=truth(E,sub,fb);labelsec=time.process_time()-start
            actual,measured=kernel(E,fb,sub[1:],name)
            assert actual==labels
            row={"phase":phase,"curve_id":rec["curve_id"],"multiplier":mult,"actual_usable_points":len(fb),"nonidentity_targets":len(sub)-1,"support_nonidentity":cert["support_nonidentity"],"ordered_tuples":cert["ordered_tuples"],"projection_group_additions":base["projection_group_additions"],"base_cpu_seconds":basesec,"label_replay_cpu_seconds":labelsec,"curve_setup_cpu_seconds":curve_setup,"all_targets_semantic_replay":True,**measured}
            row["fitness_including_projection"]=row["unit_weight_work"]+base["projection_group_additions"]
            rows.append(row);inputs.append({"phase":phase,"multiplier":mult,"kernel":name,"curve":rec,"base":base,"targets":[point(P) for P in sub[1:]],"certificate":cert})
            with (HERE/"program-group-raw.jsonl").open("a") as f:f.write(json.dumps(row,sort_keys=True)+"\n")
        if phase=="training":
            B=next(x["actual_usable_points"] for x in rows if x["multiplier"]==1)
            eligible=[x for x in rows if x["actual_usable_points"]==B and B>0]
            if not eligible:save("program-group-results.json",{"rows":rows,"status":"empty baseline prevents nondegenerate selection"});return
            selected=min(eligible,key=lambda x:(x["fitness_including_projection"],x["multiplier"],x["kernel"]))
            save("program-group-selected-before-heldout.json",{"selected":selected,"training_rows_sha256":digest(rows)})
    save("program-group-inputs.json",inputs)
    save("program-group-results.json",{"rows":rows,"selected":selected,"total_search_and_holdout_cpu_seconds":time.process_time()-t,"search_and_holdout_counted_work":sum(x["fitness_including_projection"] for x in rows),"all_targets_replayed":True,"scope":"actual group-law kernels, cofactor-projected bases, counted stage operations; no full IC speedup"})
    print(json.dumps({"selected":selected,"heldout":rows[-2:]}))
if __name__=="__main__":main()
