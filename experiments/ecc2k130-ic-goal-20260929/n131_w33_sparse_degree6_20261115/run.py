"""Supervise two frozen sparse degree-six arms and preserve censored rows."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/"run_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_SPARSE_DEGREE6_RUN"
for name,digest in cfg["sha256"].items():
    assert sha(HERE/name)==digest,name
assert not (HERE/"run_result.json").exists()
rows=[]
for arm in cfg["arms"]:
    index=arm["target_index"]
    command=[str(HERE/"sparse_degree6"),str(HERE/f"equations_{index}.txt"),
             str(cfg["rows_requested_per_arm"]),arm["mode"],
             str(cfg["child_limit_seconds"])]
    stdout=HERE/f"arm_{index}.stdout"
    stderr=HERE/f"arm_{index}.stderr"
    assert not stdout.exists() and not stderr.exists()
    started=time.monotonic()
    with stdout.open("w") as out,stderr.open("w") as err:
        child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        process=psutil.Process(child.pid)
        peak_rss=0
        parent_stop=None
        while child.poll() is None:
            try:
                peak_rss=max(peak_rss,process.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            elapsed=time.monotonic()-started
            if peak_rss>cfg["rss_cap_bytes"]:
                parent_stop="EXTERNAL_MEMORY_CAP"
            elif elapsed>cfg["parent_limit_seconds_per_arm"]:
                parent_stop="EXTERNAL_TIMEOUT"
            if parent_stop:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL)
                break
            time.sleep(0.2)
        exit_code=child.wait()
    text=stdout.read_text().strip()
    parsed=None
    if exit_code==0 and text:
        parsed=json.loads(text.splitlines()[-1])
        assert parsed["target_index"]==index
        status=parsed["status"]
    else:
        status=parent_stop or "PRODUCER_FAILURE"
    row={"target_index":index,"name":arm["name"],"command":command,
         "status":status,"exit_code":exit_code,"parent_stop":parent_stop,
         "parent_wall_seconds":time.monotonic()-started,
         "peak_child_rss_sample_bytes":peak_rss,
         "stdout_sha256":sha(stdout),"stderr_sha256":sha(stderr),
         "child_result":parsed}
    rows.append(row)
    print(json.dumps({"target_index":index,"status":status,
                      "rows_processed":None if parsed is None else parsed["rows_processed"],
                      "parent_wall_seconds":row["parent_wall_seconds"]},sort_keys=True),flush=True)
result={"status":"COMPLETE_SPARSE_DEGREE6_SUPERVISION",
        "candidate_id":None,"curve_id":cfg["curve_id"],
        "protocol_sha256":sha(HERE/"run_protocol.json"),
        "rows":rows}
(HERE/"run_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
