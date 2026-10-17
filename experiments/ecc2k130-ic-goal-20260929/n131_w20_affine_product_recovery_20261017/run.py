"""One-worker monitored N131 affine-product pair-oracle query."""
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
p=json.loads((HERE/'protocol.json').read_text())
for path,digest in p['sources'].items():assert sha(path)==digest,path
command=[str(HERE/'affine'),p['fixture'],p['support'],p['valid_bitmap'],
         str(HERE/'native_result.json'),str(p['native_cap_seconds']),
         str(p['rss_cap_bytes']),str(p['rotation'])]
parent=psutil.Process(os.getpid())
start=time.monotonic();peak=0;stop=None;monitor_failures=0
with (HERE/'native.stdout').open('x') as out,(HERE/'native.stderr').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:peak=max(peak,parent.memory_info().rss+proc.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:monitor_failures+=1
        if peak>p['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic()-start>p['parent_cap_seconds']:stop='PARENT_CAP'
        if stop:
            os.killpg(child.pid,signal.SIGTERM)
            break
        time.sleep(.1)
    child.wait()
try:native=json.loads((HERE/'native_result.json').read_text())
except (FileNotFoundError,json.JSONDecodeError):native=None
status=('COMPLETE' if child.returncode==0 and not stop and monitor_failures==0 and
        native and native['status']=='COMPLETE_AFFINE_PAIR_RECOVERY'
        else 'BOUNDED_UNKNOWN' if stop or native and native['status']=='CENSORED_TIME'
        else 'PRODUCER_FAILURE')
record={'status':status,'command':command,'exit_code':child.returncode,
        'stop_reason':stop,'monitor_failures':monitor_failures,
        'sampled_peak_combined_rss_bytes':peak,
        'parent_wall_seconds':time.monotonic()-start,
        'protocol_sha256':sha(HERE/'protocol.json'),
        'stdout_sha256':sha(HERE/'native.stdout'),
        'stderr_sha256':sha(HERE/'native.stderr'),
        'native_result_sha256':sha(HERE/'native_result.json') if native else None,
        'candidate_id':None}
with (HERE/'receipt.json').open('x') as f:
    json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
print(status,record['parent_wall_seconds'],peak,flush=True)
