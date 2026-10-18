#!/usr/bin/env python3
"""Independent result/identity consistency checks; does not rerun timed workloads."""
import ast,collections,hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from curve_identity import curve_identity
def read(n):return json.loads((HERE/n).read_text())
def main():
    checks=[]
    for p in HERE.glob("*.py"):ast.parse(p.read_text());checks.append({"check":"syntax","source":p.name,"passed":True})
    records={}
    for line in (HERE/"prefilter-inputs.jsonl").read_text().splitlines():
        x=json.loads(line);rec=x["curve"];cid=rec["curve_id"]
        ident=curve_identity(rec["field"],rec["curve"],re.search(r"^EC1N[0-9]+C([a-z][a-z0-9]*)h[a-f0-9]+$",cid)[1])
        assert ident["curve_id"]==cid
        records[cid]={**rec,**ident}
        assert sum(x["multiplicity"])==len(x["factor_base_scalars"])**3
        for k,w in x["positive_witnesses"].items():assert sum(w)%len(x["subgroup_points"])==int(k)
    for x in read("program-group-inputs.json"):
        rec=x["curve"];cid=rec["curve_id"];ident=curve_identity(rec["field"],rec["curve"],re.search(r"^EC1N[0-9]+C([a-z][a-z0-9]*)h[a-f0-9]+$",cid)[1]);assert ident["curve_id"]==cid
        records[cid]={**rec,**ident}
        assert sum(x["certificate"]["multiplicity"])==len(x["base"]["projected_points"])**3
    checks.append({"check":"exact curve identities and yield tuple conservation","curves":len(records),"passed":True})
    (HERE/"curve-records.json").write_text(json.dumps(list(records.values()),indent=2,sort_keys=True)+"\n")
    raw=[json.loads(t) for t in (HERE/"sat-raw.jsonl").read_text().splitlines()]
    assert len(raw)==88 and all(r["oracle_agreement"] for r in raw)
    assert all(("-b" in r["command"])==(r["policy"]=="paper") for r in raw)
    assert all(sorted(r["branch_order"])==list(range(1,3*r["cell"]["ell"]+1)) for r in raw)
    checks.append({"check":"all WDSat answers independently oracle-checked; permutations and symmetry gate","calls":len(raw),"passed":True})
    bucket=read("bucket-results.json")
    for r in bucket["rows"]:
        for g in [r["statistic"]]+([r["matched_sha_null"]] if "matched_sha_null" in r else []):
            assert sum(g["denominators"])==g["ordered_pairs"]
            assert all(sum(row)==den for row,den in zip(g["numerators"],g["denominators"]))
            assert abs(g["max_pi"]-g["numerator"]/g["denominator"])<1e-12
            assert g["maximum_fft_rounding_residual"]<1e-6
            ratios=[num/den for row,den in zip(g["numerators"],g["denominators"]) if den for num in row]
            assert abs(max(ratios)*g["effective_M"]-g["gain_effective"])<1e-10
        if r["filter"]=="halving-trace":assert r["statistic"]["gain_effective"]==1
    checks.append({"check":"exact bucket denominators, maxima, trace and rounding gates","rows":len(bucket["rows"]),"passed":True})
    corpus=read("surrogate-corpus.json");groups=collections.defaultdict(set)
    for r in corpus:groups[r["shape_sha256"]].add(r["split"])
    assert all(len(v)==1 for v in groups.values())
    assert len({r["run_id"] for r in corpus})==len(corpus)
    assert all(r["degree_target"] is None for r in corpus if not r["complete"])
    cc=read("surrogate-curve-results.json")
    sets=[set(v) for v in cc["curves"].values()]
    assert len(set.union(*sets))==sum(map(len,sets))
    assert all(m["unbounded"] and m["quantile_rank"]>m["calibration_curve_count"] for m in cc["models"])
    checks.append({"check":"receipt uniqueness, shape and curve separation, censoring and conformal rank","cells":len(corpus),"passed":True})
    for launchname in ["prefilter-launch.json","sat-launch.json","bucket-launch.json","program-group-launch.json","surrogate-launch.json","surrogate-curve-launch.json"]:
        x=read(launchname);h=x.get("source_sha256",x.get("sources"))
        if isinstance(h,dict):
            for name,expected in h.items():
                p=Path(name)
                if not p.is_absolute():p=HERE/name if (HERE/name).exists() else ROOT/name
                assert p.exists(),p
                assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,(launchname,str(p))
        elif isinstance(h,str):assert hashlib.sha256((HERE/"surrogate.py").read_bytes()).hexdigest()==h
    checks.append({"check":"executed source digests still match launch receipts","passed":True})
    out={"passed":True,"checks":checks,"scope":"independent consistency/identity recheck; source workloads retain their group-law replay certificates","not_claimed":["full IC recovery","formal UNSAT trace","new mathematical invariant","independent rerun of timings","all audit acceptance criteria complete"]}
    (HERE/"verify.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
