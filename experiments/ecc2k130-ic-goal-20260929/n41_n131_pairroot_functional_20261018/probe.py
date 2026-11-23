"""Frozen alternating fixed-conflict comparison of quadratic and functional gates."""
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE=Path(__file__).resolve().parent
p=json.loads((HERE/"probe_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path,digest in p["sources"].items():
    assert sha(path)==digest,path
assert not (HERE/"probe_result.json").exists()
assert p["arms"]==["quadratic","functional","functional","quadratic"]
assert p["worker_count"]==1
results=[]
parent=psutil.Process(os.getpid())
for index,arm in enumerate(p["arms"]):
    formula=Path(p["formulas"][arm])
    command=[p["solver"],"--threads=1",f"--maxconfl={p['max_conflicts']}",
             f"--maxtime={p['solver_wall_cap_seconds']}",
             "--zero-exit-status","--verb=1","--printsol=1",str(formula)]
    stdout=HERE/f"probe_{index}_{arm}.stdout"
    stderr=HERE/f"probe_{index}_{arm}.stderr"
    start=time.monotonic()
    peak=0
    samples=0
    stop=None
    monitor_error=None
    with stdout.open("xb") as out,stderr.open("xb") as err:
        child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        observed=psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak=max(peak,parent.memory_info().rss+observed.memory_info().rss)
                samples+=1
            except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError) as exc:
                if child.poll() is None:
                    monitor_error=type(exc).__name__
                    stop="MONITOR_FAILURE"
                    break
            if peak>p["rss_cap_bytes"]:
                stop="RSS_CAP"
                break
            if time.monotonic()-start>p["parent_wall_cap_seconds"]:
                stop="WALL_CAP"
                break
            time.sleep(.1)
        if stop and child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
        exit_code=child.wait()
    wall=time.monotonic()-start
    stream=stdout.read_text(errors="replace")
    if stop:
        status="BOUNDED_UNKNOWN" if stop=="WALL_CAP" else stop
    elif "s SATISFIABLE" in stream:
        status="SAT_MODEL_UNVERIFIED"
    elif "s UNSATISFIABLE" in stream:
        status="UNSAT_UNVERIFIED"
    elif "s INDETERMINATE" in stream:
        status="INDETERMINATE_CONFLICT_CAP"
    else:
        status="PRODUCER_FAILURE_NO_TERMINAL_STATUS"
    conflicts=re.findall(r"^c conflicts\s*:\s*(\d+)",stream,re.M)
    decisions=re.findall(r"^c decisions\s*:\s*(\d+)",stream,re.M)
    propagations=re.findall(r"^c propagations\s*:\s*(\S+)",stream,re.M)
    restarts=[line for line in stream.splitlines() if line.startswith("c rst")]
    result={"arm":arm,"arm_index":index,"status":status,"stop_reason":stop,
            "command":command,"solver_exit_code":exit_code,
            "wall_seconds":wall,"sampled_peak_combined_rss_bytes":peak,
            "rss_samples":samples,"monitor_error":monitor_error,
            "reported_conflicts":int(conflicts[-1]) if conflicts else None,
            "reported_decisions":int(decisions[-1]) if decisions else None,
            "reported_propagations":propagations[-1] if propagations else None,
            "last_restart_line":restarts[-1] if restarts else None,
            "solver_stdout_sha256":sha(stdout),"solver_stderr_sha256":sha(stderr),
            "protocol_sha256":sha(HERE/"probe_protocol.json")}
    (HERE/f"probe_{index}_{arm}_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    results.append(result)
    print(json.dumps({k:result[k] for k in ("arm_index","arm","status","wall_seconds",
                                            "reported_conflicts","reported_propagations")},sort_keys=True),flush=True)
    if status=="SAT_MODEL_UNVERIFIED":
        break
out={"status":"COMPLETED_FROZEN_ABBA_PROBE" if len(results)==4 else "EARLY_TERMINAL_MODEL",
     "candidate_id":None,"curve_id":p["curve_id"],
     "max_conflicts":p["max_conflicts"],"arm_results":results,
     "protocol_sha256":sha(HERE/"probe_protocol.json")}
(HERE/"probe_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
