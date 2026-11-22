"""Freeze source identity, resource cap, and panel before the Sage producer."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def row(path):
    path=path.resolve()
    return {"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
assert not (HERE/"protocol.json").exists()
sources={
    "panel":ROOT/"n41_n131_rr_code_family_span_20261017/panel_n131_v2.json",
    "sixpair":ROOT/"n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json",
    "public":ROOT/"n131_w23_sixpair_public_sat_20261017/protocol.json",
    "prior_x_sets":ROOT/"n41_n131_triple_x_prefix_capacity_20261023/x_sets_v2.json",
    "run":HERE/"run_sage.py",
    "runtime":HERE/"sage_runtime_info.json",
}
p={"schema":"n131_w23_triple_x_quadratic_capacity_v1",
   "status":"FROZEN_BEFORE_PRODUCER",
   "curve_id":"EC1N131Ckb1heb5f1998f20b",
   "seed_mask":898618,"family_cap":320,"mask_scan_cap":10000,
   "checkpoints":[1,2,3,4,5,8,16,32,64,128,192,256,320],
   "source_rule":"first four archived source-valid families, then ascending canonical mask from 47; both endpoints source valid and distinct folded columns disjoint from fixed slots 1..5",
   "feature_rule":"131 linear bits and 8515 distinct pairwise bit products of triple-sum x; affine hull of exact 32 x values per family",
   "workload":"constructed six-pair residual and two previously archived ordinary raw-point residuals; fixed pair slots 1 and 2 and fixed suffix slots 3..5",
   "one_worker":True,"wall_cap_seconds":600,"rss_cap_bytes":4294967296,
   "rss_cap_kind":"sampled self-process guard checked each family",
   "sources":{name:row(path) for name,path in sources.items()}}
(HERE/"protocol.json").write_text(json.dumps(p,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":p["status"],"sources":{k:v["sha256"] for k,v in p["sources"].items()}}))
