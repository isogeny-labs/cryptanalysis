"""Bind existing N131 source, export code, and bounded sparse experiment."""
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
 "coefficients":ROOT/"n131_w33_freecode_resultant_20261018/coefficients.json",
 "prior_runner":ROOT/"n131_w33_block_macaulay_20261019/run_n131.py",
 "prior_core":ROOT/"n41_w11_block_macaulay_20261019/run.py",
 "macaulay_core":ROOT/"n41_n131_macaulay_family_gate_20261019/macaulay.py",
 "prior_audit":ROOT/"n131_w33_block_macaulay_20261019/audit_result.json",
 "prepare":HERE/"prepare.py",
}
p={"schema":"n131_w33_sparse_degree6_v1",
   "status":"FROZEN_BEFORE_W33_SPARSE_EXPORT",
   "curve_id":"EC1N131Ckb1heb5f1998f20b",
   "target_indices":[0,1],"degree":6,"variables":34,
   "one_worker":True,"wall_cap_seconds_per_target":180,
   "rss_cap_bytes":4294967296,
   "positive_control":{"left_code":3,"right_code":16722},
   "sources":{name:row(path) for name,path in sources.items()}}
(HERE/"protocol.json").write_text(json.dumps(p,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":p["status"],"sources":{k:v["sha256"] for k,v in p["sources"].items()}},sort_keys=True))
