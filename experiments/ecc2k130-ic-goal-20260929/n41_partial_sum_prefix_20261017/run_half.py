"""Monitored exact half-code join and prefix census."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((HERE/'half_protocol.json').read_text())
for name,digest in p['sha256'].items():assert sha(HERE/name)==digest,name
source=HERE.parent/'n41_sixpair_shared_target_20261017/join_input.tsv'
assert sha(source)==p['source_sha256']
parent=psutil.Process(os.getpid())
begin=time.monotonic();peak=0;stop=None;live_monitor_failures=0
with (HERE/'half_stdout.txt').open('x') as out,(HERE/'half_stderr.txt').open('x') as err:
    child=subprocess.Popen([str(HERE/'half'),str(source)],stdout=out,stderr=err,
                           start_new_session=True)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak=max(peak,parent.memory_info().rss+proc.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:live_monitor_failures+=1
        if peak>p['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic()-begin>p['wall_cap_seconds']:stop='WALL_CAP'
        if stop:
            os.killpg(child.pid,signal.SIGTERM)
            break
        time.sleep(.05)
    child.wait()
text=(HERE/'half_stdout.txt').read_text()
try:payload=json.loads(text) if child.returncode==0 and not stop else None
except json.JSONDecodeError:payload=None
status='COMPLETE' if payload and not live_monitor_failures else 'BOUNDED_UNKNOWN' if stop else 'PRODUCER_FAILURE'
record={'status':status,'worker_exit':child.returncode,'stop_reason':stop,
        'live_monitor_failures':live_monitor_failures,'sampled_peak_combined_rss_bytes':peak,
        'parent_wall_seconds':time.monotonic()-begin,
        'protocol_sha256':sha(HERE/'half_protocol.json'),
        'stdout_sha256':sha(HERE/'half_stdout.txt'),'stderr_sha256':sha(HERE/'half_stderr.txt'),
        'worker':payload,'candidate_id':None}
with (HERE/'half_result.json').open('x') as f:
    json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
print(status,record['parent_wall_seconds'],peak,live_monitor_failures,flush=True)
