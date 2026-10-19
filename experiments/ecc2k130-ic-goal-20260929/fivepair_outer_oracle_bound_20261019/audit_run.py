"""Frozen sorted-vector replay of the exact N41 right-sum set."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"audit_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_SORTED_N41_RIGHT_SUPPORT_AUDIT"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
producer=json.loads((HERE/"run_v2_result.json").read_text())
assert producer["status"]=="COMPLETE_N41_RIGHT_SUPPORT"
cmd=[cfg["sources"]["binary"]["path"],cfg["sources"]["input"]["path"]]
started=time.monotonic()
try:
    run=subprocess.run(cmd,capture_output=True,timeout=cfg["wall_cap_seconds"])
    stdout,stderr=run.stdout,run.stderr
    exit_code=run.returncode
    status="PRODUCER_FAILURE"
    if exit_code==0:
        row=json.loads(stdout)
        assert row["status"]=="PASS_SORTED_N41_RIGHT_SUPPORT"
        assert row["distinct_sums"]==producer["row"]["distinct_sums"]
        assert row["compatible_pairs"]==producer["row"]["compatible_pairs"]
        status="PASS_SORTED_N41_RIGHT_SUPPORT_AUDIT"
except subprocess.TimeoutExpired as exc:
    stdout,stderr=exc.stdout or b"",exc.stderr or b""
    exit_code=None
    status="WALL_CAP_PARTIAL_AUDIT"
(HERE/"audit.stdout").write_bytes(stdout)
(HERE/"audit.stderr").write_bytes(stderr)
result={"status":status,"candidate_id":None,"command":cmd,"exit_code":exit_code,
        "parent_wall_seconds":time.monotonic()-started,
        "peak_child_rss_raw":resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "rss_cap_enforcement":"post-run peak check",
        "protocol_sha256":sha(HERE/"audit_protocol.json"),
        "runner_sha256":sha(Path(__file__)),
        "stdout_sha256":sha(HERE/"audit.stdout"),"stderr_sha256":sha(HERE/"audit.stderr")}
if status=="PASS_SORTED_N41_RIGHT_SUPPORT_AUDIT":result["row"]=row
if result["peak_child_rss_raw"]>cfg["rss_cap_bytes"]:result["status"]="RSS_CAP_EXCEEDED"
(HERE/"audit_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ("status","exit_code","parent_wall_seconds","peak_child_rss_raw")},sort_keys=True))
