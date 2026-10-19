"""Run the frozen N41 right-support census under one-worker resource caps."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_N41_RIGHT_SUPPORT_CENSUS"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
cmd=[cfg["sources"]["binary"]["path"],cfg["sources"]["input"]["path"]]


def set_memory_limit():
    resource.setrlimit(resource.RLIMIT_AS,(cfg["rss_cap_bytes"],cfg["rss_cap_bytes"]))


started=time.monotonic()
status="PRODUCER_FAILURE"
try:
    run=subprocess.run(cmd,capture_output=True,timeout=cfg["wall_cap_seconds"],
                       preexec_fn=set_memory_limit)
    stdout,stderr=run.stdout,run.stderr
    exit_code=run.returncode
    if exit_code==0:
        row=json.loads(stdout)
        assert row["status"]=="COMPLETE_N41_RIGHT_SUPPORT"
        status="COMPLETE_N41_RIGHT_SUPPORT"
except subprocess.TimeoutExpired as exc:
    stdout=exc.stdout or b""
    stderr=exc.stderr or b""
    exit_code=None
    status="WALL_CAP_PARTIAL_CENSUS"
parent_wall=time.monotonic()-started
(HERE/"run.stdout").write_bytes(stdout)
(HERE/"run.stderr").write_bytes(stderr)
result={"status":status,"candidate_id":None,"command":cmd,"exit_code":exit_code,
        "parent_wall_seconds":parent_wall,"peak_child_rss_raw":resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "wall_cap_seconds":cfg["wall_cap_seconds"],"rss_cap_bytes":cfg["rss_cap_bytes"],
        "stdout_sha256":sha(HERE/"run.stdout"),"stderr_sha256":sha(HERE/"run.stderr"),
        "protocol_sha256":sha(HERE/"protocol.json"),"runner_sha256":sha(Path(__file__))}
if status=="COMPLETE_N41_RIGHT_SUPPORT":result["row"]=row
(HERE/"run_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:result[k] for k in ("status","exit_code","parent_wall_seconds","peak_child_rss_raw")},sort_keys=True))
