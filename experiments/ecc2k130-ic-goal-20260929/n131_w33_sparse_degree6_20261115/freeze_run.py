"""Freeze exact sparse binary/input identity before the two capped arms."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (HERE/"run_protocol.json").exists()
prep=json.loads((HERE/"prepare_result.json").read_text())
assert prep["status"]=="PASS_W33_SPARSE_EQUATION_EXPORT"
for row in prep["rows"]:
    assert sha(HERE/f'equations_{row["target_index"]}.txt')==row["equation_sha256"]
p={"schema":"n131_w33_sparse_degree6_run_v1",
   "status":"FROZEN_BEFORE_SPARSE_DEGREE6_RUN",
   "curve_id":"EC1N131Ckb1heb5f1998f20b",
   "arms":[{"target_index":0,"name":"constructed_positive","mode":"numeric"},
           {"target_index":1,"name":"frozen_public_raw_point","mode":"numeric"}],
   "rows_requested_per_arm":78076,"child_limit_seconds":180,
   "parent_limit_seconds_per_arm":190,"rss_cap_bytes":4294967296,
   "worker_count":1,"compiler":"c++ -O3 -std=c++17 -Wall -Wextra -pedantic",
   "compiler_version":subprocess.run(["c++","--version"],capture_output=True,text=True,
                                     check=True).stdout.splitlines()[0],
   "sha256":{name:sha(HERE/name) for name in
     ("protocol.json","prepare_result.json","equations_0.txt","equations_1.txt",
      "sparse_degree6.cpp","sparse_degree6","run.py")}}
(HERE/"run_protocol.json").write_text(json.dumps(p,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":p["status"],"sha256":p["sha256"]},sort_keys=True))
