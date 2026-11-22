"""Capped one-worker build of the public-coordinate resultant circuit."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path
import psutil

D=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((D/'protocol.json').read_text())
assert protocol['producer_sha256']==sha(D/'build.py')
assert protocol['runner_sha256']==sha(Path(__file__))
assert (D/'sage_runtime_info.json').exists()
command=['/Volumes/SSD990/cryptanalysis/sage','-python',str(D/'build.py')]
parent=psutil.Process(os.getpid())
start=time.monotonic()
peak=0;stop=None;degraded=False
with (D/'build.stdout').open('x') as out,(D/'build.stderr').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    process=psutil.Process(child.pid)
    while child.poll() is None:
        try:
            descendants=process.children(recursive=True)
            current=parent.memory_info().rss+process.memory_info().rss
            for p in descendants:current+=p.memory_info().rss
            peak=max(peak,current)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:degraded=True
        if peak>protocol['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic()-start>protocol['wall_cap_s']:stop='PARENT_WALL_CAP'
        if stop:
            os.killpg(child.pid,signal.SIGTERM)
            break
        time.sleep(.1)
    child.wait()
result=D/'build_result.json'
complete=(child.returncode==0 and result.exists() and stop is None)
status=('COMPLETE' if complete else 'RSS_BOUNDARY' if stop=='RSS_CAP'
        else 'BOUNDED_UNKNOWN' if stop=='PARENT_WALL_CAP' else 'PRODUCER_FAILURE')
receipt={'status':status,'protocol_sha256':sha(D/'protocol.json'),
         'runner_sha256':sha(Path(__file__)),'command':command,
         'exit_code':child.returncode,'stop_reason':stop,
         'parent_wall_s':time.monotonic()-start,
         'sampled_peak_combined_rss_bytes':peak,'monitor_degraded':degraded,
         'runtime_info_sha256':sha(D/'sage_runtime_info.json'),
         'stdout_sha256':sha(D/'build.stdout'),
         'stderr_sha256':sha(D/'build.stderr'),
         'build_result_sha256':sha(result) if complete else None}
(D/'build_receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('status','parent_wall_s',
                  'sampled_peak_combined_rss_bytes','exit_code','stop_reason')}))
