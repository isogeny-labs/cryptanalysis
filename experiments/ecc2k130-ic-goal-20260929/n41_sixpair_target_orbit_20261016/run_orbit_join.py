"""One-worker exact N41 target-orbit join under frozen wall and RSS caps."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
protocol=json.loads((HERE/'join_protocol.json').read_text())
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
assert sha(HERE/'run_orbit_join.py')==protocol['runner_sha256']
command=[str(HERE/'orbit_join'),protocol['input_path']]
start=time.monotonic_ns();parent=psutil.Process(os.getpid())
peak=0;degraded=False;stop=None
with (HERE/'join.stdout').open('x') as out,(HERE/'join.stderr').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:peak=max(peak,parent.memory_info().rss+proc.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:degraded=True
        if peak>protocol['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic_ns()-start>protocol['wall_cap_seconds']*10**9:stop='WALL_CAP'
        if stop:
            os.killpg(child.pid,signal.SIGTERM);break
        time.sleep(.1)
    code=child.wait()
lines=(HERE/'join.stdout').read_text().splitlines()
terminal=[line for line in lines if line.startswith('CENSUS_COMPLETE ')]
status='COMPLETE' if code==0 and len(terminal)==1 and not stop else 'BOUNDED_UNKNOWN' if stop else 'PRODUCER_FAILURE'
result={'status':status,'exit_code':code,'stop_reason':stop,'wall_ns':time.monotonic_ns()-start,
        'sampled_peak_combined_rss_bytes':peak,'monitor_degraded':degraded,
        'orbits_completed':sum(line.startswith('ORBIT_DONE ') for line in lines),
        'hits':[line for line in lines if line.startswith('ORBIT_HIT ')],
        'terminal':terminal,'protocol_sha256':sha(HERE/'join_protocol.json'),
        'stdout_sha256':sha(HERE/'join.stdout'),'stderr_sha256':sha(HERE/'join.stderr')}
(HERE/'join_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(status,result['orbits_completed'],len(result['hits']),result['wall_ns']/1e9,flush=True)
