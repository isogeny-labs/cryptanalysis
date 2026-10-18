#!/usr/bin/env python3
import hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
HERE=Path(__file__).resolve().parent
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
def main():
    if (HERE/"surrogate-curve-results.json").exists():raise SystemExit("Append-only run exists")
    corpus=json.loads((HERE/"surrogate-corpus.json").read_text())
    save("surrogate-curve-launch.json",{"argv":sys.argv,"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"source_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/"SURROGATE-CURVE-PROTOCOL.json",HERE/"surrogate-corpus.json"]}})
    ids=sorted(set(r["curve_id"] for r in corpus),key=lambda x:hashlib.sha256(("curve-holdout-20261018|"+x).encode()).digest())
    splits={"train":ids[:4],"calibration":ids[4:7],"test":ids[7:]}
    out={"curves":splits,"models":[],"claim":"Descriptive only; no exchangeability assumption for selected historical curves"}
    for target in ["degree_target","ops_target_log2"]:
        parts={s:[r for r in corpus if r["curve_id"] in ii and r[target] is not None] for s,ii in splits.items()}
        dv=DictVectorizer(sparse=False);X=dv.fit_transform([r["features"] for r in parts["train"]]);y=np.array([r[target] for r in parts["train"]])
        rf=RandomForestRegressor(n_estimators=64,max_depth=8,min_samples_leaf=2,random_state=20261018,n_jobs=1)
        t=time.process_time();rf.fit(X,y);fit=time.process_time()-t
        cp=rf.predict(dv.transform([r["features"] for r in parts["calibration"]]));cy=np.array([r[target] for r in parts["calibration"]]);maxres=[]
        for cid in splits["calibration"]:
            rr=[abs(a-b) for r,a,b in zip(parts["calibration"],cy,cp) if r["curve_id"]==cid]
            if rr:maxres.append({"curve_id":cid,"maximum_absolute_residual":max(rr)})
        rank=math.ceil((len(maxres)+1)*.9);q=None if rank>len(maxres) else sorted(r["maximum_absolute_residual"] for r in maxres)[rank-1]
        tp=rf.predict(dv.transform([r["features"] for r in parts["test"]]));ty=np.array([r[target] for r in parts["test"]])
        out["models"].append({"target":target,"train_cells":len(y),"calibration_cells":len(cy),"test_cells":len(ty),"calibration_curve_count":len(maxres),"quantile_rank":rank,"interval_half_width":q,"unbounded":q is None,"mae":float(np.mean(np.abs(ty-tp))),"training_median_mae":float(np.mean(np.abs(ty-np.median(y)))),"fit_cpu_seconds":fit,"per_curve_residuals":maxres,"predictions":[{"run_id":r["run_id"],"curve_id":r["curve_id"],"observed":float(y),"predicted":float(p)} for r,y,p in zip(parts["test"],ty,tp)]})
    save("surrogate-curve-results.json",out);print(json.dumps({"curves":splits,"models":[{k:v for k,v in m.items() if k not in ["predictions","per_curve_residuals"]} for m in out["models"]]}))
if __name__=="__main__":main()
