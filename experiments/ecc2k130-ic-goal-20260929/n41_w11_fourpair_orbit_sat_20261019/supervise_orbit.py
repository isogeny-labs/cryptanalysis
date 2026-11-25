"""One-worker bounded CryptoMiniSat query with raw transcript preservation."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'orbit_query_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_W11_ORBIT41_SAT_QUERY'
for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
assert cfg['worker_count']==1
out=HERE/'orbit_solver.stdout';err=HERE/'orbit_solver.stderr';receipt=HERE/'orbit_query_result.json'
assert not out.exists() and not err.exists() and not receipt.exists()
cmd=[cfg['solver'],*cfg['solver_flags'],cfg['sources']['formula']['path']]
start=time.monotonic();parent=psutil.Process(os.getpid());peak=samples=0;stop=None
with out.open('xb') as fo,err.open('xb') as fe:
    child=subprocess.Popen(cmd,stdout=fo,stderr=fe,cwd=HERE,start_new_session=True)
    (HERE/'orbit_query_handle.json').write_text(json.dumps({'pid':child.pid,'command':cmd,
        'started_monotonic':start},sort_keys=True,indent=2)+'\n')
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:peak=max(peak,parent.memory_info().rss+proc.memory_info().rss);samples+=1
        except psutil.NoSuchProcess:
            if child.poll() is not None:break
            stop='MONITOR_FAILURE';break
        except (psutil.AccessDenied,PermissionError):
            if child.poll() is None:stop='MONITOR_FAILURE';break
        if peak>cfg['rss_cap_bytes']:stop='RSS_CAP';break
        if time.monotonic()-start>cfg['wall_cap_seconds']:stop='WALL_CAP';break
        time.sleep(.02)
    if stop and child.poll() is None:child.terminate()
    code=child.wait()
lines=out.read_text(errors='replace').splitlines()
sat=any(line.strip()=='s SATISFIABLE' for line in lines)
unsat=any(line.strip()=='s UNSATISFIABLE' for line in lines)
assert not (sat and unsat)
status=('SAT_MODEL_PENDING_AUDIT' if sat and not stop else
        'UNSAT_SOLVER_STATUS' if unsat and not stop else stop or 'BOUNDED_UNKNOWN')
result={'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],
        'command':cmd,'exit_code':code,'wall_seconds':time.monotonic()-start,
        'sampled_peak_combined_rss_bytes':peak,'rss_samples':samples,
        'stop_reason':stop,'terminal_sat_line':sat,'terminal_unsat_line':unsat,
        'stdout_sha256':sha(out),'stderr_sha256':sha(err),
        'protocol_sha256':sha(HERE/'orbit_query_protocol.json'),
        'supervisor_sha256':sha(__file__)}
receipt.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','exit_code','wall_seconds',
    'sampled_peak_combined_rss_bytes','stop_reason')},sort_keys=True))
