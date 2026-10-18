#!/usr/bin/env python3
"""Receipt-aware aggregate-cell surrogate; censoring never becomes an exact label."""
import collections
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
def main():
    if (HERE/"surrogate-results.json").exists():raise SystemExit("Append-only run already exists")
    paths=sorted((ROOT/"experiments/pdp-degree-heuristics/results").glob("*.jsonl"))
    receipt={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    save("surrogate-launch.json",{"argv":sys.argv,"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"protocol_sha256":hashlib.sha256((HERE/"PROTOCOL.json").read_bytes()).hexdigest(),"input_sha256":receipt,"mode":"CPU-only exploratory analysis of archived aggregates; not an IC performance run"})
    raw=[];rejected=[];byid=collections.defaultdict(list)
    for p in paths:
        for line,text in enumerate(p.read_text().splitlines(),1):
            d=json.loads(text);src={"source":str(p.relative_to(ROOT)),"line":line,"receipt_sha256":sha(d)}
            if d.get("schema")!="pdp-degree-profile/1":
                rejected.append({**src,"reason":"different degree semantics/schema"});continue
            byid[d["run_id"]].append((d,src))
    duplicates=0
    for rid,rr in byid.items():
        unique={src["receipt_sha256"] for _,src in rr}
        if len(unique)>1:
            for d,src in rr:rejected.append({**src,"run_id":rid,"reason":"conflicting reused run_id; no arbitrarily selected observation"})
            continue
        duplicates+=len(rr)-1
        d,src=rr[0]
        good=(d.get("curve_id") and d.get("factor_base_sha256") and d.get("workload",{}).get("targets_sha256") and d.get("provenance",{}).get("sources") and d.get("workload_id") and d.get("stage_config_id"))
        if not good:
            rejected.append({**src,"run_id":rid,"reason":"missing identity/workload/source receipt binding"});continue
        c=d["cell"];deg=d.get("degrees",{}).get("mxl",{});cost=d.get("cost",{}).get("mxl",{})
        hist=deg.get("D_solve_hist",{})
        numeric={int(k):int(v) for k,v in hist.items() if str(k).isdigit() and int(v)>0}
        counts=d.get("counts",{})
        censored=int(deg.get("censored",0))
        incomplete=any(int(counts.get(k,0))>0 for k in ["pdp_timeout","pdp_budget","pdp_error"])
        complete=(censored==0 and not incomplete and sum(numeric.values())==int(counts.get("ordinary_queries",-1)))
        form=c.get("formulation",d.get("point_decomposition",{}).get("formulation","direct"))
        order=d["point_decomposition"]["monomial_order"]
        shape={"curve_id":d["curve_id"],"n":int(c["n"]),"ell":int(c["l"]),"m":int(c["m"]),"family":c["family"],"formulation":form,"order":order}
        group=int(sha(shape),16)%5
        features={"n":int(c["n"]),"ell":int(c["l"]),"m":int(c["m"]),"N":int(c["N"]),"family":c["family"],"formulation":form,"order":order,"mode":"mxl"}
        ops=cost.get("ops_per_attempt_mean")
        raw.append({**src,"run_id":rid,"workload_id":d["workload_id"],"stage_config_id":d["stage_config_id"],"curve_id":d["curve_id"],"factor_base_sha256":d["factor_base_sha256"],"implementation_sha256":d["provenance"].get("implementation_sha256"),"features":features,"shape_sha256":sha(shape),"split":"test" if group==0 else "calibration" if group==1 else "train","complete":complete,"censored":censored,"recorded_status_counts":counts,"degree_histogram":hist,"maximum_observed_degree":max(numeric) if numeric else None,"degree_target":max(numeric) if complete and numeric else None,"ops_target_log2":math.log2(ops) if complete and ops and ops>0 else None,"observed_ops_per_attempt":ops,"memory_response":None,"memory_missing_reason":"main-process high-water RSS is not a per-cell matrix-memory label","target_count":int(counts.get("ordinary_queries",0))})
    save("surrogate-corpus.json",raw)
    save("surrogate-rejected.json",rejected)
    out={"input_rows":sum(len(x) for x in byid.values()),"unique_run_ids":len(byid),"exact_duplicate_rows_removed":duplicates,"accepted_cells":len(raw),"rejected_rows":len(rejected),"split_counts":dict(collections.Counter(x["split"] for x in raw)),"complete_cells":sum(x["complete"] for x in raw),"censored_or_incomplete_cells":sum(not x["complete"] for x in raw),"models":[],"coverage_status":"empirical diagnostic only: historical nonrandom cells are not exchangeable; no extrapolation coverage guarantee","receipt_limit":"source/workload/base identities are retained and conflicting reused run IDs quarantined. Individual targets and executable historical source snapshots are not reconstructed here; corpus does not satisfy the full requested all-receipt promotion gate."}
    for target in ["degree_target","ops_target_log2"]:
        parts={s:[r for r in raw if r["split"]==s and r[target] is not None] for s in ["train","calibration","test"]}
        if min(map(len,parts.values()))<10:
            out["models"].append({"target":target,"status":"insufficient split data","counts":{s:len(r) for s,r in parts.items()}});continue
        dv=DictVectorizer(sparse=False)
        X=dv.fit_transform([r["features"] for r in parts["train"]]);y=np.array([r[target] for r in parts["train"]])
        for modelname,model in [("training-median",None),("random-forest-64-depth-8",RandomForestRegressor(n_estimators=64,max_depth=8,min_samples_leaf=2,random_state=20261018,n_jobs=1))]:
            t=time.process_time()
            if model is not None:model.fit(X,y)
            fitsec=time.process_time()-t
            def predict(rows):
                return np.full(len(rows),np.median(y)) if model is None else model.predict(dv.transform([r["features"] for r in rows]))
            cp=predict(parts["calibration"]);cy=np.array([r[target] for r in parts["calibration"]]);resid=np.abs(cy-cp)
            rank=math.ceil((len(resid)+1)*.9)
            q=float(np.sort(resid)[rank-1]) if rank<=len(resid) else None
            t=time.process_time();tp=predict(parts["test"]);infersec=time.process_time()-t
            ty=np.array([r[target] for r in parts["test"]]);covered=np.abs(ty-tp)<=q if q is not None else np.ones(len(ty),dtype=bool)
            predictions=[{"run_id":r["run_id"],"curve_id":r["curve_id"],"shape_sha256":r["shape_sha256"],"observed":float(v),"predicted":float(p),"lower":float(p-q) if q is not None else None,"upper":float(p+q) if q is not None else None,"covered":bool(ok)} for r,v,p,ok in zip(parts["test"],ty,tp,covered)]
            out["models"].append({"target":target,"model":modelname,"train_cells":len(y),"calibration_cells":len(cy),"test_cells":len(ty),"quantile_rank":rank,"interval_half_width":q,"empirical_coverage":float(covered.mean()),"mae":float(np.abs(ty-tp).mean()),"fit_cpu_seconds":fitsec,"heldout_inference_cpu_seconds":infersec,"predictions":predictions})
    # All incomplete observations remain in the independent completion classifier.
    parts={s:[r for r in raw if r["split"]==s] for s in ["train","test"]}
    if min(map(len,parts.values()))>=10:
        dv=DictVectorizer(sparse=False);X=dv.fit_transform([r["features"] for r in parts["train"]]);y=[int(r["complete"]) for r in parts["train"]]
        rf=RandomForestClassifier(n_estimators=64,max_depth=8,min_samples_leaf=2,class_weight="balanced",random_state=20261018,n_jobs=1)
        t=time.process_time();rf.fit(X,y);fitsec=time.process_time()-t
        pred=rf.predict(dv.transform([r["features"] for r in parts["test"]]));truth=np.array([int(r["complete"]) for r in parts["test"]])
        out["completion_model"]={"target":"recorded cell completion under historical limits","test_cells":len(truth),"accuracy":float((truth==pred).mean()),"constant_majority_accuracy":float(max(sum(truth),len(truth)-sum(truth))/len(truth)),"false_complete":int(((pred==1)&(truth==0)).sum()),"fit_cpu_seconds":fitsec,"limitation":"historical resource limits/target counts affect this label; no guarantee of future completion"}
    proto=json.loads((HERE/"PROTOCOL.json").read_text())
    out["prospective_cells"]=[{**c,"status":"rejected as unsupported","reason":"unseen chained presentation and/or n/ell outside admitted aggregate-cell support; do not quote calibrated interval"} for c in proto["surrogate"]["prospective"]]
    save("surrogate-results.json",out)
    print(json.dumps({k:v for k,v in out.items() if k not in ("models","completion_model")}))

if __name__=="__main__":main()
