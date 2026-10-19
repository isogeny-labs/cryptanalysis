"""Run exact 41-orientation W11 group census under one-worker caps."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'query_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_W11_ORBIT_CENSUS'
for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
assert cfg['worker_count']==1 and cfg['target_orientations']==41
out=HERE/'census.stdout';err=HERE/'census.stderr';receipt=HERE/'query_result.json'
assert not out.exists() and not err.exists() and not receipt.exists()
cmd=[cfg['binary'],cfg['sources']['join_input']['path'],'41']
start=time.monotonic();parent=psutil.Process(os.getpid());peak=samples=0;stop=None
with out.open('xb') as fo,err.open('xb') as fe:
    child=subprocess.Popen(cmd,stdout=fo,stderr=fe,cwd=HERE,start_new_session=True)
    (HERE/'query_handle.json').write_text(json.dumps({'pid':child.pid,'command':cmd,
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
lines=out.read_text().splitlines()
terminal=next((x for x in reversed(lines) if x.startswith('TOTAL_HITS ') or x.startswith('NO_HIT ')),None)
status=('COMPLETE_CENSUS' if not stop and code==0 and terminal else stop or 'PRODUCER_FAILURE')
result={'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],
    'command':cmd,'exit_code':code,'stop_reason':stop,
    'wall_seconds':time.monotonic()-start,
    'sampled_peak_combined_rss_bytes':peak,'rss_samples':samples,
    'terminal_line':terminal,'hit_lines':sum(x.startswith('HIT ') for x in lines),
    'orientation_done_lines':sum(x.startswith('ORIENTATION_DONE ') for x in lines),
    'stdout_sha256':sha(out),'stderr_sha256':sha(err),
    'protocol_sha256':sha(HERE/'query_protocol.json'),
    'supervisor_sha256':sha(__file__)}
receipt.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','exit_code','wall_seconds',
    'sampled_peak_combined_rss_bytes','terminal_line')},sort_keys=True))
