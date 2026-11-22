"""Freeze an independent low-pivot audit of the complete producer census."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def row(path):
    path=path.resolve()
    return {"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
assert not (HERE/"audit_protocol.json").exists()
sources={
    "panel":ROOT/"n41_n131_rr_code_family_span_20261017/panel_n131_v2.json",
    "sixpair":ROOT/"n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json",
    "public":ROOT/"n131_w23_sixpair_public_sat_20261017/protocol.json",
    "prior_x_sets":ROOT/"n41_n131_triple_x_prefix_capacity_20261023/x_sets_v2.json",
    "producer":HERE/"result.json",
    "auditor":HERE/"audit_sage.py",
    "runtime":HERE/"sage_runtime_info.json",
}
p={"schema":"n131_w23_triple_x_quadratic_audit_v1",
   "status":"FROZEN_BEFORE_INDEPENDENT_AUDIT",
   "seed_mask":898618,"wall_cap_seconds":600,"rss_cap_bytes":4294967296,
   "sources":{name:row(path) for name,path in sources.items()}}
(HERE/"audit_protocol.json").write_text(json.dumps(p,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":p["status"],"sources":{k:v["sha256"] for k,v in p["sources"].items()}}))
