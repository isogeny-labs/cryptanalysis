"""Bound one checked-Sage N131 sign-norm query under frozen resource caps."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
case=sys.argv[1]
assert case in ("positive","public")
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/("run_protocol_"+case+".json")).read_text())
assert cfg["status"]=="FROZEN_BEFORE_N131_SIGN_NORM_"+case.upper()
assert cfg["worker_count"]==1
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
receipt_path=HERE/(case+"_receipt.json")
assert not receipt_path.exists()
command=[cfg["sage_launcher"],"-python",str(HERE/"sign_norm_sage.py"),case]
parent=psutil.Process(os.getpid())
started=time.monotonic()
peak=samples=0
stop=monitor_error=None
stdout=HERE/(case+".stdout")
stderr=HERE/(case+".stderr")
with stdout.open("xb") as out,stderr.open("xb") as err:
    child=subprocess.Popen(command,cwd="/Volumes/SSD990/cryptanalysis",
                           stdout=out,stderr=err,start_new_session=True)
    (HERE/(case+"_handle.json")).write_text(json.dumps(
        {"pid":child.pid,"command":command,"started_monotonic":started},
        sort_keys=True,indent=2)+"\n")
    observed=psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak=max(peak,parent.memory_info().rss+observed.memory_info().rss)
            samples+=1
        except psutil.NoSuchProcess:
            if child.poll() is not None:
                break
            time.sleep(.1)
            if child.poll() is not None:
                break
            stop="MONITOR_FAILURE"
            monitor_error="NoSuchProcessWhileLive"
            break
        except (psutil.AccessDenied,PermissionError) as exc:
            if child.poll() is None:
                stop="MONITOR_FAILURE"
                monitor_error=type(exc).__name__
                break
        if peak>cfg["rss_cap_bytes"]:
            stop="RSS_CAP"
            break
        if time.monotonic()-started>cfg["wall_cap_seconds"]:
            stop="WALL_CAP"
            break
        time.sleep(.1)
    if stop and child.poll() is None:
        child.terminate()
    exit_code=child.wait()
result_path=HERE/(case+"_result.json")
coeff_path=HERE/(case+"_coefficients.json")
status=("COMPLETE" if not stop and exit_code==0 and result_path.exists() and coeff_path.exists()
        else stop or "PRODUCER_FAILURE")
receipt={"status":status,"candidate_id":None,"case":case,
         "curve_id":cfg["curve_id"],"command":command,"child_pid":child.pid,
         "exit_code":exit_code,"stop_reason":stop,"monitor_error":monitor_error,
         "wall_seconds":time.monotonic()-started,
         "sampled_peak_combined_rss_bytes":peak,"rss_samples":samples,
         "stdout_sha256":sha(stdout),"stderr_sha256":sha(stderr),
         "result_sha256":sha(result_path) if result_path.exists() else None,
         "coefficients_sha256":sha(coeff_path) if coeff_path.exists() else None,
         "protocol_sha256":sha(HERE/("run_protocol_"+case+".json"))}
receipt_path.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
print(json.dumps({key:receipt[key] for key in ("case","status","wall_seconds",
                                           "sampled_peak_combined_rss_bytes")},sort_keys=True))
